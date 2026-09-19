; ============================================================
; DCE Pro - Export Form 2 to DXF
; ============================================================
; Hướng dẫn:
; 1. Mở AutoCAD
; 2. Tool > AutoLISP > Load Application
; 3. Chọn file này
; 4. Gõ lệnh: exportform2
; ============================================================

(defun c:exportform2 (/)
  (princ "\n[INFO] Exporting Form 2 to DXF...")

  (setq dwg_path "C:\\DCE Pro\\Cad\\Form 2.dwg")
  (setq dxf_path "C:\\DCE Pro\\Cad\\Form 2.dxf")

  ; Check file exists
  (if (findfile dwg_path)
    (progn
      ; Open DWG
      (princ "\n[1/3] Opening Form 2.dwg...")
      (command "_.OPEN" dwg_path)

      ; Export to DXF
      (princ "\n[2/3] Exporting to DXF...")
      (command "_.DXFOUT" dxf_path "" "" "" "")

      ; Close without saving
      (princ "\n[3/3] Closing...")
      (command "_.CLOSE" "_N")

      (princ (strcat "\n[DONE] Saved: " dxf_path))
    )
    (princ "\n[ERROR] File not found: C:\\DCE Pro\\Cad\\Form 2.dwg")
  )

  (princ)
)

; Export Form 2_Steel
(defun c:exportform2s (/)
  (princ "\n[INFO] Exporting Form 2_Steel to DXF...")

  (setq dwg_path "C:\\DCE Pro\\Cad\\Form 2_Steel.dwg")
  (setq dxf_path "C:\\DCE Pro\\Cad\\Form 2_Steel.dxf")

  (if (findfile dwg_path)
    (progn
      (princ "\n[1/3] Opening Form 2_Steel.dwg...")
      (command "_.OPEN" dwg_path)

      (princ "\n[2/3] Exporting to DXF...")
      (command "_.DXFOUT" dxf_path "" "" "" "")

      (princ "\n[3/3] Closing...")
      (command "_.CLOSE" "_N")

      (princ (strcat "\n[DONE] Saved: " dxf_path))
    )
    (princ "\n[ERROR] File not found")
  )

  (princ)
)

; Export ALL forms at once
(defun c:exportallforms (/)
  (princ "\n[INFO] Exporting ALL DCE Pro forms to DXF...")

  (setq forms (list
    (list "Form 2" "C:\\DCE Pro\\Cad\\Form 2.dwg" "C:\\DCE Pro\\Cad\\Form 2.dxf")
    (list "Form 2_Steel" "C:\\DCE Pro\\Cad\\Form 2_Steel.dwg" "C:\\DCE Pro\\Cad\\Form 2_Steel.dxf")
    (list "Form 3" "C:\\DCE Pro\\Cad\\Form 3.dwg" "C:\\DCE Pro\\Cad\\Form 3.dxf")
    (list "Form 3_Steel" "C:\\DCE Pro\\Cad\\Form 3_Steel.dwg" "C:\\DCE Pro\\Cad\\Form 3_Steel.dxf")
    (list "Form 4" "C:\\DCE Pro\\Cad\\Form 4.dwg" "C:\\DCE Pro\\Cad\\Form 4.dxf")
    (list "Form 4_Steel" "C:\\DCE Pro\\Cad\\Form 4_Steel.dwg" "C:\\DCE Pro\\Cad\\Form 4_Steel.dxf")
    (list "Form 5" "C:\\DCE Pro\\Cad\\Form 5.dwg" "C:\\DCE Pro\\Cad\\Form 5.dxf")
    (list "Form 5_Steel" "C:\\DCE Pro\\Cad\\Form 5_Steel.dwg" "C:\\DCE Pro\\Cad\\Form 5_Steel.dxf")
  ))

  (foreach f forms
    (setq name (car f))
    (setq dwg (cadr f))
    (setq dxf (caddr f))

    (princ (strcat "\n[Processing] " name "..."))

    (if (findfile dwg)
      (progn
        (command "_.OPEN" dwg)
        (command "_.DXFOUT" dxf "" "" "" "")
        (command "_.CLOSE" "_N")
        (princ " OK")
      )
      (princ " SKIP (file not found)")
    )
  )

  (princ "\n[COMPLETE] All forms exported to C:\\DCE Pro\\Cad\\")
  (princ)
)

; ============================================================
; SHOW LAYERS & BLOCKS
; ============================================================
(defun c:showform2info (/)
  (princ "\n[INFO] Analyzing Form 2...")

  (setq dwg_path "C:\\DCE Pro\\Cad\\Form 2.dwg")

  (if (findfile dwg_path)
    (progn
      (command "_.OPEN" dwg_path)

      (princ "\n--- LAYERS ---")
      (vlax-for layer (vla-get-Layers (vla-get-ActiveDocument (vlax-get-acad-object)))
        (princ (strcat "\n  " (vla-get-Name layer)
                " | Color: " (itoa (vla-get-Color layer))
                " | LType: " (vla-get-LinetypeName layer)))
      )

      (princ "\n\n--- BLOCKS ---")
      (vlax-for block (vla-get-Blocks (vla-get-ActiveDocument (vlax-get-acad-object)))
        (if (not (wcmatch (vla-get-Name block) "*MODEL*,*PAPER*"))
          (princ (strcat "\n  " (vla-get-Name block))))
      )

      (command "_.CLOSE" "_N")
      (princ "\n[COMPLETE]")
    )
    (princ "\n[ERROR] File not found")
  )

  (princ)
)

(princ "\n[OK] DCE Pro export scripts loaded.")
(princ "\nCommands:")
(princ "\n  exportform2       - Export Form 2 to DXF")
(princ "\n  exportform2s      - Export Form 2_Steel to DXF")
(princ "\n  exportallforms    - Export ALL forms to DXF")
(princ "\n  showform2info     - Show layers & blocks of Form 2")
(princ)
