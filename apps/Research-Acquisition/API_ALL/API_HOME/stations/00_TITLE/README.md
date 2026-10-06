# 00_TITLE

Runs first in every CKG routine. Renames a source to
`<Author code> <YYYY-MM-DD> · <Title> · <Keyword>, <Keyword> · <Move>`, writes std_title / keywords / move /
upload_date / original_file into its YAML, and adds its classifications to the master record
(`faiththruphysics.com\00_CLASSIFICATION_MASTER.md`; data in `tools\taxonomy.json`). See tools/standard_title.py.
