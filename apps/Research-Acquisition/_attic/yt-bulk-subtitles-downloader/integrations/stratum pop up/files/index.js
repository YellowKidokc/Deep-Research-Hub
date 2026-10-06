// Stratum Cloud Worker — API for sync + AI proxy
// Deploy: wrangler deploy
// D1 binding: STRATUM_DB
// Secret: CLAUDE_API_KEY, STRATUM_AUTH_TOKEN

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    // CORS for PWA
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders() });
    }

    // Auth check
    const token = request.headers.get('Authorization')?.replace('Bearer ', '');
    if (token !== env.STRATUM_AUTH_TOKEN) {
      return json({ error: 'unauthorized' }, 401);
    }

    try {
      // ── CLIPS ──
      if (path === '/api/clips' && request.method === 'GET') {
        const limit = url.searchParams.get('limit') || 50;
        const pinned = url.searchParams.get('pinned');
        const slot = url.searchParams.get('slot');

        let query = 'SELECT * FROM clips';
        const params = [];
        const conditions = [];

        if (pinned === '1') conditions.push('pinned = 1');
        if (slot !== null && slot !== undefined && slot !== '') {
          conditions.push('slot = ?');
          params.push(parseInt(slot));
        }
        if (conditions.length) query += ' WHERE ' + conditions.join(' AND ');
        query += ' ORDER BY pinned DESC, created_at DESC LIMIT ?';
        params.push(parseInt(limit));

        const result = await env.STRATUM_DB.prepare(query).bind(...params).all();
        return json(result.results);
      }

      if (path === '/api/clips' && request.method === 'POST') {
        const body = await request.json();
        const id = crypto.randomUUID().slice(0, 16);
        await env.STRATUM_DB.prepare(
          `INSERT INTO clips (id, content, source, pinned, tags, slot, device_id)
           VALUES (?, ?, ?, ?, ?, ?, ?)`
        ).bind(
          id, body.content, body.source || 'manual',
          body.pinned ? 1 : 0, JSON.stringify(body.tags || []),
          body.slot ?? null, body.device_id || null
        ).run();
        return json({ id, status: 'created' }, 201);
      }

      if (path.startsWith('/api/clips/') && request.method === 'DELETE') {
        const id = path.split('/').pop();
        await env.STRATUM_DB.prepare('DELETE FROM clips WHERE id = ?').bind(id).run();
        return json({ status: 'deleted' });
      }

      // ── PROMPTS ──
      if (path === '/api/prompts' && request.method === 'GET') {
        const cat = url.searchParams.get('category');
        let query = 'SELECT * FROM prompts';
        const params = [];
        if (cat) { query += ' WHERE category = ?'; params.push(cat); }
        query += ' ORDER BY usage_count DESC, name ASC';
        const result = await env.STRATUM_DB.prepare(query).bind(...params).all();
        return json(result.results);
      }

      if (path === '/api/prompts' && request.method === 'POST') {
        const body = await request.json();
        const id = crypto.randomUUID().slice(0, 16);
        await env.STRATUM_DB.prepare(
          `INSERT INTO prompts (id, name, content, category, hotkey)
           VALUES (?, ?, ?, ?, ?)`
        ).bind(id, body.name, body.content, body.category || 'general', body.hotkey || null).run();
        return json({ id, status: 'created' }, 201);
      }

      if (path.startsWith('/api/prompts/') && request.method === 'PUT') {
        const id = path.split('/').pop();
        const body = await request.json();
        await env.STRATUM_DB.prepare(
          `UPDATE prompts SET name = ?, content = ?, category = ?, hotkey = ?, updated_at = datetime('now')
           WHERE id = ?`
        ).bind(body.name, body.content, body.category, body.hotkey || null, id).run();
        return json({ status: 'updated' });
      }

      if (path.startsWith('/api/prompts/') && request.method === 'DELETE') {
        const id = path.split('/').pop();
        await env.STRATUM_DB.prepare('DELETE FROM prompts WHERE id = ?').bind(id).run();
        return json({ status: 'deleted' });
      }

      // ── LINKS ──
      if (path === '/api/links' && request.method === 'GET') {
        const result = await env.STRATUM_DB.prepare(
          'SELECT * FROM links ORDER BY usage_count DESC, title ASC'
        ).all();
        return json(result.results);
      }

      if (path === '/api/links' && request.method === 'POST') {
        const body = await request.json();
        const id = crypto.randomUUID().slice(0, 16);
        await env.STRATUM_DB.prepare(
          `INSERT INTO links (id, title, url, category, hotkey, icon) VALUES (?, ?, ?, ?, ?, ?)`
        ).bind(id, body.title, body.url, body.category || 'general', body.hotkey || null, body.icon || null).run();
        return json({ id, status: 'created' }, 201);
      }

      // ── SHORTCUTS ──
      if (path === '/api/shortcuts' && request.method === 'GET') {
        const result = await env.STRATUM_DB.prepare(
          'SELECT * FROM shortcuts WHERE enabled = 1 ORDER BY trigger_key'
        ).all();
        return json(result.results);
      }

      if (path === '/api/shortcuts' && request.method === 'POST') {
        const body = await request.json();
        const id = crypto.randomUUID().slice(0, 16);
        await env.STRATUM_DB.prepare(
          `INSERT INTO shortcuts (id, trigger_key, action, target, device_scope)
           VALUES (?, ?, ?, ?, ?)`
        ).bind(id, body.trigger_key, body.action, body.target || null, body.device_scope || 'all').run();
        return json({ id, status: 'created' }, 201);
      }

      // ── AI PROXY ──
      // Keeps API key server-side, PWA never sees it
      if (path === '/api/ai' && request.method === 'POST') {
        const body = await request.json();
        const aiResponse = await fetch('https://api.anthropic.com/v1/messages', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'x-api-key': env.CLAUDE_API_KEY,
            'anthropic-version': '2023-06-01',
          },
          body: JSON.stringify({
            model: body.model || 'claude-sonnet-4-6',
            max_tokens: body.max_tokens || 1024,
            system: body.system || '',
            messages: body.messages,
          }),
        });

        const aiData = await aiResponse.json();

        // Log to history
        const inputText = body.messages.map(m => m.content).join('\n');
        const outputText = aiData.content?.map(c => c.text || '').join('\n') || '';
        await env.STRATUM_DB.prepare(
          `INSERT INTO ai_history (id, input_text, output_text, model, prompt_id, tokens_in, tokens_out)
           VALUES (?, ?, ?, ?, ?, ?, ?)`
        ).bind(
          crypto.randomUUID().slice(0, 16),
          inputText.slice(0, 2000), outputText.slice(0, 5000),
          body.model || 'claude-sonnet-4-6', body.prompt_id || null,
          aiData.usage?.input_tokens || 0, aiData.usage?.output_tokens || 0
        ).run();

        return json(aiData);
      }

      // ── SYNC STATUS ──
      if (path === '/api/sync/status' && request.method === 'GET') {
        const counts = await env.STRATUM_DB.prepare(`
          SELECT 
            (SELECT COUNT(*) FROM clips) as clips,
            (SELECT COUNT(*) FROM prompts) as prompts,
            (SELECT COUNT(*) FROM links) as links,
            (SELECT COUNT(*) FROM shortcuts) as shortcuts,
            (SELECT COUNT(*) FROM ai_history) as ai_calls
        `).first();
        return json(counts);
      }

      return json({ error: 'not found' }, 404);

    } catch (err) {
      return json({ error: err.message }, 500);
    }
  }
};

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...corsHeaders(), 'Content-Type': 'application/json' },
  });
}

function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  };
}
