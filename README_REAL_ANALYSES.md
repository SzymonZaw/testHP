# Real analysis boundary

This branch formalizes the output contract: the UI reports only measurements that are actually computed from readable local files. Image files may yield raster dimensions and RGB/brightness statistics; tabular/RNA-like files may yield inspected row counts and numeric distributions; JSON annotations may yield structural node counts. These are descriptive input measurements, not biological findings.

A biological result is reported only when a modality-specific validated analysis exists, has its required input, and was actually executed. Otherwise the UI reports `not available` together with the concrete limitation. No probability, diagnosis, score, cohort relationship, or subject-level link is synthesized from filenames, dataset names, placeholders, or missing files.
