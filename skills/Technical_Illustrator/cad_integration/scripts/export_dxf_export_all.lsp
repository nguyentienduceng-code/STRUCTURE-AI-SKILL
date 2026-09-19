; ============================================================
; DCE Pro Forms - Export All to DXF
; ============================================================
; Huong dan:
; 1. Mo AutoCAD
; 2. Tool > AutoLISP > Load Application
; 3. Chon file nay: export_dxf.lsp
; 4. Go lenh: (c:export_all_forms)
; ============================================================

(defun c:export_all_forms (/ forms_list out_path)
  (setq forms_list (list
    (list "Form 2" "C:\\DCE Pro\\Cad\\Form 2.dwg" "C:\\DCE Pro\\Cad\\Form 2.dxf")
    (list "Form 2_Steel" "C:\\DCE Pro\\Cad\\Form 2_Steel.dwg" "C:\\DCE Pro\\Cad\\Form 2_Steel.dxf")
    (list "Form 3" "C:\\DCE Pro\\Cad\\Form 3.dwg" "C:\\DCE Pro\\Cad\\Form 3.dxf")
    (list "Form 3_Steel" "C:\\DCE Pro\\Cad\\Form 3_Steel.dwg" "C:\\DCE Pro\\Cad\\Form 3_Steel.dxf")
    (list "Form 4" "C:\\DCE Pro\\Cad\\Form 4.dwg" "C:\\DCE Pro\\Cad\\Form 4.dxf")
    (list "Form 4_Steel" "C:\\DCE Pro\\Cad\\Form 4_Steel.dwg" "C:\\DCE Pro\\Cad\\Form 4_Steel.dxf")
    (list "Form 5" "C:\\DCE Pro\\Cad\\Form 5.dwg" "C:\\DCE Pro\\Cad\\Form 5.dxf")
    (list "Form 5_Steel" "C:\\DCE Pro\\Cad\\Form 5_Steel.dwg" "C:\\DCE Pro\\Cad\\Form 5_Steel.dxf")
  ))

  (princ "\n=== DCE Pro Forms - Export to DXF ===")
  (princ "\nStarting export...")

  (foreach form forms_list
    (setq name (car form))
    (setq dwg_path (cadr form))
    (setq dxf_path (caddr form))

    (princ (strcat "\nProcessing: " name "..."))

    ; Check if file exists
    (if (findfile dwg_path)
      (progn
        ; Open DWG file
        (command "_.OPEN" dwg_path)

        ; Export to DXF
        (command "_.DXFOUT" dxf_path)

        ; Close without saving
        (command "_.CLOSE" "_N")

        (princ "OK")
      )
      (progn
        (princ (strcat "ERROR - File not found: " dwg_path))
      )
    )
  )

  (princ "\n=== Export Complete ===")
  (princ)
)

; Export Form 2 only (for testing)
(defun c:export_form2 (/ dwg_path dxf_path)
  (setq dwg_path "C:\\DCE Pro\\Cad\\Form 2.dwg")
  (setq dxf_path "C:\\DCE Pro\\Cad\\Form 2.dxf")

  (princ "\nExporting Form 2...")

  (if (findfile dwg_path)
    (progn
      (command "_.OPEN" dwg_path)
      (command "_.DXFOUT" dxf_path)
      (command "_.CLOSE" "_N")
      (princ (strcat "\nDone: " dxf_path))
    )
    (princ "\nERROR: File not found!")
  )
  (princ)
)

; ============================================================
; PHÂN TÍCH LAYERS, BLOCKS, ENTITIES
; ============================================================
(defun c:analyze_forms (/ doc)
  (princ "\n=== DCE Pro Forms Analysis ===")

  ; Get current document
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))

  (princ "\n--- LAYERS ---")
  (vlax-for layer (vla-get-Layers doc)
    (princ (strcat "\n  " (vla-get-Name layer)
            " | Color: " (itoa (vla-get-Color layer))
            " | Linetype: " (vla-get-LinetypeName layer)))
  )

  (princ "\n--- BLOCKS ---")
  (vlax-for block (vla-get-Blocks doc)
    (if (not (wcmatch (vla-get-Name block) "*MODEL*,*PAPER*"))
      (princ (strcat "\n  " (vla-get-Name block))))
  )

  (princ "\n--- DIMENSION STYLES ---")
  (vlax-for dimstyle (vla-get-DimStyles doc)
    (princ (strcat "\n  " (vla-get-Name dimstyle)))
  )

  (princ "\n--- TEXT STYLES ---")
  (vlax-for style (vla-get-TextStyles doc)
    (princ (strcat "\n  " (vla-get-Name style)))
  )

  (princ "\n=== Analysis Complete ===")
  (princ)
)

; ============================================================
; SHOW LAYER INFO FOR ALL FORMS
; ============================================================
(defun c:show_all_layers (/ forms_list doc)
  (setq forms_list (list
    "C:\\DCE Pro\\Cad\\Form 2.dwg"
    "C:\\DCE Pro\\Cad\\Form 2_Steel.dwg"
    "C:\\DCE Pro\\Cad\\Form 3.dwg"
    "C:\\DCE Pro\\Cad\\Form 3_Steel.dwg"
    "C:\\DCE Pro\\Cad\\Form 4.dwg"
    "C:\\DCE Pro\\Cad\\Form 4_Steel.dwg"
    "C:\\DCE Pro\\Cad\\Form 5.dwg"
    "C:\\DCE Pro\\Cad\\Form 5_Steel.dwg"
  ))

  (princ "\n=== Layer Analysis for All Forms ===")

  (foreach dwg_path forms_list
    (princ (strcat "\n\n--- " dwg_path " ---"))

    (if (findfile dwg_path)
      (progn
        (command "_.OPEN" dwg_path)
        (c:analyze_forms)
        (command "_.CLOSE" "_N")
      )
      (princ (strcat "\n  ERROR: File not found"))
    )
  )

  (princ "\n=== Done ===")
  (princ)
)

(princ "\n[OK] DCE Pro DXF Export loaded.")
(princ "\nCommands:")
(princ "\n  (c:export_all_forms)  - Export all forms to DXF")
(princ "\n  (c:export_form2)      - Export Form 2 only")
(princ "\n  (c:analyze_forms)     - Analyze current drawing")
(princ "\n  (c:show_all_layers)    - Analyze all forms")
(princ)
