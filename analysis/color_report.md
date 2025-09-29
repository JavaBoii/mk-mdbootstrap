# Farb-Analyse Report

## Theme-Farben & Paletten

### Theme-Farben
- **danger** (33 Vorkommen) – Layer: bootstrap-core, mdb-free
- **dark** (236 Vorkommen) – Layer: bootstrap-core, mdb-free
- **info** (28 Vorkommen) – Layer: bootstrap-core, mdb-free
- **light** (103 Vorkommen) – Layer: bootstrap-core, mdb-free
- **primary** (34 Vorkommen) – Layer: bootstrap-core, mdb-free
- **secondary** (50 Vorkommen) – Layer: bootstrap-core, mdb-free
- **success** (33 Vorkommen) – Layer: bootstrap-core, mdb-free
- **warning** (30 Vorkommen) – Layer: bootstrap-core, mdb-free

### Palettenfarben
- **amber** (15 Tokens)
- **blue** (73 Tokens)
- **brown** (11 Tokens)
- **cyan** (41 Tokens)
- **deep-orange** (15 Tokens)
- **deep-purple** (15 Tokens)
- **green** (58 Tokens)
- **indigo** (41 Tokens)
- **light-blue** (15 Tokens)
- **light-green** (15 Tokens)
- **lime** (15 Tokens)
- **orange** (56 Tokens)
- **pink** (43 Tokens)
- **purple** (60 Tokens)
- **red** (49 Tokens)
- **teal** (41 Tokens)
- **yellow** (41 Tokens)

## Berechnungsregeln für States

- **active** (121 Tokens) – Funktionen: mix, rgb, rgba, shift-color, tint-color; Beispiele: $accordion-button-active-bg (bootstrap-core), $accordion-button-active-bg (bootstrap-core), $accordion-button-active-bg (mdb-free), $accordion-button-active-color (bootstrap-core), $accordion-button-active-color (bootstrap-core) … (+116 weitere)
- **checked** (60 Tokens) – Funktionen: rgb, rgba; Beispiele: $form-check-input-checkbox-checked-after-border-color (mdb-free), $form-check-input-checkbox-checked-after-border-width (mdb-free), $form-check-input-checkbox-checked-after-height (mdb-free), $form-check-input-checkbox-checked-after-margin-left (mdb-free), $form-check-input-checkbox-checked-after-margin-top (mdb-free) … (+55 weitere)
- **disabled** (59 Tokens) – Funktionen: rgb, rgba; Beispiele: $btn-close-disabled-opacity (bootstrap-core), $btn-close-disabled-opacity (bootstrap-core), $btn-disabled-opacity (bootstrap-core), $btn-disabled-opacity (bootstrap-core), $btn-link-disabled-color (bootstrap-core) … (+54 weitere)
- **emphasis** (54 Tokens) – Funktionen: shade-color, tint-color; Beispiele: $body-emphasis-color (bootstrap-core), $body-emphasis-color (bootstrap-core), $body-emphasis-color-dark (bootstrap-core), $body-emphasis-color-dark (bootstrap-core), $danger-text-emphasis (bootstrap-core) … (+49 weitere)
- **focus** (129 Tokens) – Funktionen: color-contrast, mix, rgb, rgba, shift-color, tint-color; Beispiele: $accordion-button-focus-border-color (bootstrap-core), $accordion-button-focus-border-color (bootstrap-core), $accordion-button-focus-box-shadow (bootstrap-core), $accordion-button-focus-box-shadow (bootstrap-core), $accordion-button-focus-box-shadow (mdb-free) … (+124 weitere)
- **hover** (96 Tokens) – Funktionen: color-contrast, hsl, mix, rgb, rgba, shade-color, shift-color, tint-color; Beispiele: $breadcrumb-item-hover-color (mdb-free), $btn-close-hover-opacity (bootstrap-core), $btn-close-hover-opacity (bootstrap-core), $btn-hover-bg-shade-amount (bootstrap-core), $btn-hover-bg-shade-amount (bootstrap-core) … (+91 weitere)
- **indeterminate** (19 Tokens) – Funktionen: keine Farb-Funktionen; Beispiele: $form-check-input-indeterminate-bg-color (bootstrap-core), $form-check-input-indeterminate-bg-color (bootstrap-core), $form-check-input-indeterminate-bg-image (bootstrap-core), $form-check-input-indeterminate-bg-image (bootstrap-core), $form-check-input-indeterminate-border-color (bootstrap-core) … (+14 weitere)
- **subtle** (108 Tokens) – Funktionen: mix, shade-color, tint-color; Beispiele: $danger-bg-subtle (bootstrap-core), $danger-bg-subtle (bootstrap-core), $danger-bg-subtle (mdb-free), $danger-bg-subtle-dark (bootstrap-core), $danger-bg-subtle-dark (bootstrap-core) … (+103 weitere)

## Wichtigste Overrides

- $hover-background (scss-var) in src/scss/bootstrap-rtl-fix/_buttons.scss überschreibt src/scss/bootstrap-rtl-fix/_buttons.scss [bootstrap-core]
- $extend-breakpoint (scss-var) in src/scss/bootstrap-rtl-fix/_containers.scss überschreibt src/scss/bootstrap-rtl-fix/_containers.scss [bootstrap-core]
- --bs-position (css-var) in src/scss/bootstrap-rtl-fix/_dropdown.scss überschreibt src/scss/bootstrap-rtl-fix/_dropdown.scss [bootstrap-core]
- $factor (scss-var) in src/scss/bootstrap-rtl-fix/_functions.scss überschreibt src/scss/bootstrap-rtl-fix/_functions.scss [bootstrap-core]
- $max-ratio (scss-var) in src/scss/bootstrap-rtl-fix/_functions.scss überschreibt src/scss/bootstrap-rtl-fix/_functions.scss [bootstrap-core]
- $max-ratio-color (scss-var) in src/scss/bootstrap-rtl-fix/_functions.scss überschreibt src/scss/bootstrap-rtl-fix/_functions.scss [bootstrap-core]
- $precision (scss-var) in src/scss/bootstrap-rtl-fix/_functions.scss überschreibt src/scss/bootstrap-rtl-fix/_functions.scss [bootstrap-core]
- $prev-key (scss-var) in src/scss/bootstrap-rtl-fix/_functions.scss überschreibt src/scss/bootstrap-rtl-fix/_functions.scss [bootstrap-core]
- $prev-num (scss-var) in src/scss/bootstrap-rtl-fix/_functions.scss überschreibt src/scss/bootstrap-rtl-fix/_functions.scss [bootstrap-core]
- $quotient (scss-var) in src/scss/bootstrap-rtl-fix/_functions.scss überschreibt src/scss/bootstrap-rtl-fix/_functions.scss [bootstrap-core]
- $remainder (scss-var) in src/scss/bootstrap-rtl-fix/_functions.scss überschreibt src/scss/bootstrap-rtl-fix/_functions.scss [bootstrap-core]
- $remainder (scss-var) in src/scss/bootstrap-rtl-fix/_functions.scss überschreibt src/scss/bootstrap-rtl-fix/_functions.scss [bootstrap-core]
- $result (scss-map) in src/scss/bootstrap-rtl-fix/_functions.scss überschreibt src/scss/bootstrap-rtl-fix/_functions.scss [bootstrap-core]
- $return-calc (scss-var) in src/scss/bootstrap-rtl-fix/_functions.scss überschreibt src/scss/bootstrap-rtl-fix/_functions.scss [bootstrap-core]
- $string (scss-var) in src/scss/bootstrap-rtl-fix/_functions.scss überschreibt src/scss/bootstrap-rtl-fix/_functions.scss [bootstrap-core]
- $infix (scss-var) in src/scss/bootstrap-rtl-fix/_list-group.scss überschreibt src/scss/bootstrap-rtl-fix/_dropdown.scss [bootstrap-core]
- $infix (scss-var) in src/scss/bootstrap-rtl-fix/_modal.scss überschreibt src/scss/bootstrap-rtl-fix/_dropdown.scss [bootstrap-core]
- $infix (scss-var) in src/scss/bootstrap-rtl-fix/_navbar.scss überschreibt src/scss/bootstrap-rtl-fix/_dropdown.scss [bootstrap-core]
- $infix (scss-var) in src/scss/bootstrap-rtl-fix/_offcanvas.scss überschreibt src/scss/bootstrap-rtl-fix/_dropdown.scss [bootstrap-core]
- $infix (scss-var) in src/scss/bootstrap-rtl-fix/_offcanvas.scss überschreibt src/scss/bootstrap-rtl-fix/_dropdown.scss [bootstrap-core]
- … 1667 weitere Overrides
