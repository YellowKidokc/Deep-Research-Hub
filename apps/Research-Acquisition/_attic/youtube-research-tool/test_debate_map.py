"""Tests for the debate mapper.

Anything that would call a model is stubbed - these cover the logic that has
to be right regardless of what the LLM says.
"""

import debate_map as dm
import debate_runner as dr


class FakeResult:
    """Stands in for a VideoInfo from search_videos."""

    def __init__(self, id, title="t", channel="c", duration=600, view_count=100):
        self.id = id
        self.title = title
        self.channel = channel
        self.duration = duration
        self.view_count = view_count
        self.url = f"https://www.youtube.com/watch?v={id}"


# ------------------------------------------------------------- candidates

def test_collect_candidates_dedupes_across_queries():
    hits = {"q1": [FakeResult("aaa"), FakeResult("bbb")],
            "q2": [FakeResult("bbb"), FakeResult("ccc")]}
    out = dm.collect_candidates(
        [("q1", "for"), ("q2", "against")],
        lambda q, limit: hits[q],
    )
    assert [c.video_id for c in out] == ["aaa", "bbb", "ccc"]


def test_collect_candidates_excludes_the_seed():
    out = dm.collect_candidates(
        [("q", "for")],
        lambda q, limit: [FakeResult("seed"), FakeResult("other")],
        exclude_ids={"seed"},
    )
    assert [c.video_id for c in out] == ["other"]


def test_collect_candidates_drops_short_clips():
    out = dm.collect_candidates(
        [("q", "for")],
        lambda q, limit: [FakeResult("short", duration=45), FakeResult("long", duration=900)],
        min_duration=240,
    )
    assert [c.video_id for c in out] == ["long"]


def test_collect_candidates_survives_a_failing_search():
    def boom(q, limit):
        if q == "bad":
            raise RuntimeError("search exploded")
        return [FakeResult("ok")]

    out = dm.collect_candidates([("bad", "x"), ("good", "y")], boom)
    assert [c.video_id for c in out] == ["ok"]


def test_candidate_carries_the_side_hint():
    out = dm.collect_candidates([("q", "critical")], lambda q, limit: [FakeResult("v")])
    assert out[0].side_hint == "critical"


# ---------------------------------------------------------------- clusters

def test_cluster_without_embeddings_falls_back_to_word_overlap(monkeypatch):
    monkeypatch.setattr(dm.oc, "embed", lambda text, model=None: None)
    claims = [
        dm.Claim(text="slavery was regulated by biblical law", side="A"),
        dm.Claim(text="biblical law regulated slavery closely", side="B"),
        dm.Claim(text="the economy depended on cotton exports", side="A"),
    ]
    clusters = dm.cluster_claims(claims)
    assert len(clusters) == 2
    assert clusters[0].is_crux and sorted(clusters[0].sides) == ["A", "B"]


def test_cruxes_sort_ahead_of_single_side_clusters(monkeypatch):
    monkeypatch.setattr(dm.oc, "embed", lambda text, model=None: None)
    claims = [
        dm.Claim(text="unique solitary isolated assertion here", side="A"),
        dm.Claim(text="shared contested disputed point alpha", side="A"),
        dm.Claim(text="shared contested disputed point alpha", side="B"),
    ]
    clusters = dm.cluster_claims(claims)
    assert clusters[0].is_crux is True


def test_cluster_of_one_side_is_not_a_crux():
    c = dm.ClaimCluster(label="x", claims=[dm.Claim(text="y")], sides=["A"])
    assert c.is_crux is False


def test_empty_claims_cluster_to_nothing():
    assert dm.cluster_claims([]) == []


# -------------------------------------------------------------- grouping

def test_group_by_side_skips_neutral_and_unclassified():
    claims = [
        dm.Claim(text="a", side="Critic"),
        dm.Claim(text="b", side="Neutral"),
        dm.Claim(text="c", side="Unclassified"),
        dm.Claim(text="d", side=""),
        dm.Claim(text="e", side="Critic"),
    ]
    grouped = dm.group_by_side(claims)
    assert list(grouped) == ["Critic"]
    assert len(grouped["Critic"]) == 2


# ------------------------------------------------------------- fallbacks

def test_fallback_queries_cover_both_directions():
    prop = dm.Proposition(statement="X is true", topic="X")
    qs = dm.fallback_queries(prop)
    hints = {h for _, h in qs}
    assert "critical" in hints and "supportive" in hints


def test_derive_proposition_returns_none_when_model_is_down(monkeypatch):
    monkeypatch.setattr(dm.oc, "generate_json", lambda *a, **k: None)
    assert dm.derive_proposition("some transcript") is None


def test_classify_stance_degrades_without_a_model(monkeypatch):
    monkeypatch.setattr(dm.oc, "generate_json", lambda *a, **k: None)
    s = dm.classify_stance(dm.Proposition(statement="p"), "text", "title", "vid")
    assert s.side == "Unclassified" and s.confidence == 0.0


def test_stance_confidence_is_clamped(monkeypatch):
    monkeypatch.setattr(dm.oc, "generate_json",
                        lambda *a, **k: {"side": "A", "confidence": 5.0})
    assert dm.classify_stance(dm.Proposition(), "t", "t", "v").confidence == 1.0


def test_stance_survives_a_non_numeric_confidence(monkeypatch):
    monkeypatch.setattr(dm.oc, "generate_json",
                        lambda *a, **k: {"side": "A", "confidence": "very"})
    assert dm.classify_stance(dm.Proposition(), "t", "t", "v").confidence == 0.0


def test_extract_claims_drops_fragments(monkeypatch):
    monkeypatch.setattr(dm.oc, "generate_json", lambda *a, **k: {
        "claims": [{"text": "too short"}, {"text": "this one is long enough to keep"}]
    })
    claims = dm.extract_claims(dm.Proposition(), "x" * 100, "vid")
    assert [c.text for c in claims] == ["this one is long enough to keep"]


def test_chunking_respects_the_cap():
    chunks = dm.chunk_text("a" * 100_000, 4000, 6)
    assert len(chunks) == 6


# ------------------------------------------------------- approval parsing

def test_enter_means_take_all():
    assert dr.parse_selection("", 10) == []


def test_n_cancels():
    assert dr.parse_selection("n", 10) is None


def test_ranges_and_lists_combine():
    assert dr.parse_selection("1,3,5-7", 10) == [1, 3, 5, 6, 7]


def test_out_of_range_picks_are_dropped():
    assert dr.parse_selection("2,99", 5) == [2]


def test_selection_with_nothing_valid_cancels():
    assert dr.parse_selection("99,100", 5) is None


def test_duplicate_picks_collapse():
    assert dr.parse_selection("3,3,3", 5) == [3]


# ------------------------------------------------- anchors and relevance

def test_anchor_terms_pick_the_discriminating_word():
    prop = dm.Proposition(
        statement="The Bible endorses slavery rather than merely regulating it",
        topic="slavery in the Bible")
    assert "slavery" in dm.anchor_terms(prop)


def test_anchor_terms_skip_generic_domain_words():
    prop = dm.Proposition(statement="The Bible says people should be good",
                          topic="bible people")
    assert "bible" not in dm.anchor_terms(prop)


def test_enforce_anchors_repairs_a_drifting_query():
    out = dm.enforce_anchors([("Bible verses against owning people", "x")], ["slavery"])
    assert out == [("Bible verses against owning people slavery", "x")]


def test_enforce_anchors_leaves_a_good_query_alone():
    out = dm.enforce_anchors([("does the bible endorse slavery", "x")], ["slavery"])
    assert out == [("does the bible endorse slavery", "x")]


def test_enforce_anchors_is_a_noop_without_anchors():
    qs = [("anything", "x")]
    assert dm.enforce_anchors(qs, []) == qs


def test_is_relevant_keeps_a_strong_score_without_the_anchor():
    assert dm.is_relevant("Leviticus 25 and the jubilee", 0.80, ["slavery"]) is True


def test_is_relevant_rejects_a_middling_score_without_the_anchor():
    # This is the real failure case: religious register, wrong topic.
    assert dm.is_relevant("Bible Verses On Arguing", 0.607, ["slavery"]) is False


def test_is_relevant_keeps_a_middling_score_that_has_the_anchor():
    assert dm.is_relevant("Why the Bible permits slavery", 0.60, ["slavery"]) is True


def test_is_relevant_rejects_anything_below_the_floor():
    assert dm.is_relevant("Talking about slavery", 0.10, ["slavery"]) is False


def test_rank_candidates_never_discards(monkeypatch):
    monkeypatch.setattr(dm.oc, "embed", lambda text, model=None: None)
    cands = [dm.Candidate(video_id=str(i), title=f"title {i}") for i in range(5)]
    ranked = dm.rank_candidates(dm.Proposition(statement="p", topic="t"), cands)
    assert len(ranked) == 5


def test_score_candidates_without_embeddings_returns_everything(monkeypatch):
    monkeypatch.setattr(dm.oc, "embed", lambda text, model=None: None)
    cands = [dm.Candidate(video_id="a", title="x"), dm.Candidate(video_id="b", title="y")]
    assert len(dm.score_candidates(dm.Proposition(), cands)) == 2


def test_score_candidates_handles_an_empty_list():
    assert dm.score_candidates(dm.Proposition(), []) == []


# --------------------------------------------------- balanced selection

def _ranked(*specs):
    """(id, side_hint, score, ok) tuples -> the shape rank_candidates returns."""
    return [(dm.Candidate(video_id=i, title=i, side_hint=h), sc, ok)
            for i, h, sc, ok in specs]


def test_balance_takes_from_every_side():
    ranked = _ranked(
        ("a1", "for", 0.9, True), ("a2", "for", 0.88, True), ("a3", "for", 0.87, True),
        ("b1", "against", 0.7, True), ("c1", "third", 0.65, True),
    )
    picked = [c.video_id for c in dm.balance_by_side(ranked, 3)]
    assert set(picked) == {"a1", "b1", "c1"}


def test_balance_does_not_return_one_sided_sets():
    # The real failure: proposition-similarity ranking favoured one side.
    ranked = _ranked(
        ("a1", "for", 0.95, True), ("a2", "for", 0.94, True),
        ("a3", "for", 0.93, True), ("a4", "for", 0.92, True),
        ("b1", "against", 0.60, True),
    )
    sides = {c.side_hint for c in dm.balance_by_side(ranked, 4)}
    assert "against" in sides


def test_balance_prefers_relevant_over_flagged():
    ranked = _ranked(("junk", "for", 0.99, False), ("good", "against", 0.60, True))
    assert dm.balance_by_side(ranked, 1)[0].video_id == "good"


def test_balance_falls_back_to_flagged_to_fill_slots():
    ranked = _ranked(("good", "for", 0.8, True), ("junk", "for", 0.5, False))
    assert len(dm.balance_by_side(ranked, 2)) == 2


def test_balance_respects_the_limit():
    ranked = _ranked(*[(f"v{i}", f"s{i % 3}", 0.9, True) for i in range(20)])
    assert len(dm.balance_by_side(ranked, 5)) == 5


def test_balance_of_nothing_is_nothing():
    assert dm.balance_by_side([], 5) == []


def test_single_side_is_detectable_from_grouping():
    """The guard in the runner keys off this: <2 sides is not a debate."""
    claims = [dm.Claim(text=f"claim {i}", side="Only Side") for i in range(20)]
    assert len(dm.group_by_side(claims)) == 1


def test_two_sides_produce_a_real_map():
    claims = [dm.Claim(text="a", side="For"), dm.Claim(text="b", side="Against")]
    assert len(dm.group_by_side(claims)) == 2


# ------------------------------------------------ proposition echo guard

def test_echo_filter_drops_the_proposition_restated(monkeypatch):
    """The real failure: the proposition came back as a load-bearing claim."""
    prop = dm.Proposition(
        statement="The Bible's depiction of human ownership is consistently condemnatory of slavery")
    vectors = {
        prop.statement: [1.0, 0.0],
        "The Bible's depiction of human ownership is consistently condemnatory of slavery": [1.0, 0.0],
        "Paul tells Philemon to receive Onesimus as a brother": [0.0, 1.0],
    }
    monkeypatch.setattr(dm.oc, "embed", lambda t, model=None: vectors.get(t))
    claims = [
        dm.Claim(text="The Bible's depiction of human ownership is consistently condemnatory of slavery"),
        dm.Claim(text="Paul tells Philemon to receive Onesimus as a brother"),
    ]
    kept = dm.drop_proposition_echo(claims, prop)
    assert [c.text for c in kept] == ["Paul tells Philemon to receive Onesimus as a brother"]


def test_echo_filter_without_embeddings_uses_word_overlap(monkeypatch):
    monkeypatch.setattr(dm.oc, "embed", lambda t, model=None: None)
    prop = dm.Proposition(statement="slavery endorsed rather regulated scripture")
    claims = [
        dm.Claim(text="slavery endorsed rather regulated scripture"),
        dm.Claim(text="completely different assertion about economics entirely"),
    ]
    assert len(dm.drop_proposition_echo(claims, prop)) == 1


def test_echo_filter_keeps_everything_without_a_proposition():
    claims = [dm.Claim(text="a"), dm.Claim(text="b")]
    assert dm.drop_proposition_echo(claims, dm.Proposition()) == claims


def test_side_case_carries_the_verified_position():
    c = dm.SideCase(side="Assigned", actual_position="What claims argue",
                    label_warning="they disagree")
    d = c.to_dict()
    assert d["actual_position"] == "What claims argue"
    assert d["label_warning"] == "they disagree"
