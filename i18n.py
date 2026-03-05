"""Internationalization strings for UI and report generation."""

UI_STRINGS: dict[str, dict] = {
    "nl": {
        "app_title": "Bonnetje Verdeler",
        "step_upload_header": "Upload AH Bonnetjes",
        "description": """\
Upload één of meerdere Albert Heijn kassabonnen en wijs elk artikel toe aan jezelf, \
je huisgenoot, of splits het als gedeeld. De app berekent precies wat je huisgenoot \
je verschuldigd is en genereert een PDF-rapport dat je kunt sturen.

**Dit gebeurt er na het uploaden:**

- **Verwerken:** Elk artikel wordt uit de PDF gehaald: naam, hoeveelheid, eenheidsprijs en eindprijs.
- **Bonuskaart kortingen:** Eventuele bonusbesparingen worden verdeeld over de kortingsartikelen, \
zodat de verdeling klopt met wat je echt hebt betaald.
- **Verdeling:** Je gaat elk artikel langs en markeert het als Van mij, Van de huisgenoot, of Gedeeld. \
Gedeelde artikelen worden 50/50 gesplitst. Je kunt ook alle artikelen tegelijk toewijzen.
- **Samenvatting en rapport:** De app telt alles op en vertelt je precies hoeveel je huisgenoot je \
verschuldigd is. Je kunt een volledig PDF-rapport downloaden om te delen.

---

**Dit werkt alleen met de PDF-bonnetjes van de Albert Heijn-app.** Deze bonnetjes zijn alleen \
beschikbaar als je je boodschappen hebt gescand met je Albert Heijn bonuskaart bij de kassa.

Zo krijg je de PDF:

1. Open de Albert Heijn-app en tik op het persoonspictogram rechtsboven.
2. Ga naar **Aankopen en bestellingen** en dan **Winkelkassabonnen**.
3. Tik op een kassabon.
4. Tik op de drie puntjes rechtsboven en kies **Kassabon delen**.
5. Sla het PDF-bestand op of stuur het naar jezelf.
""",
        "file_uploader_label": "Sleep je Albert Heijn kassabon PDFs hierheen",
        "process_button": "Verwerk Bonnetjes",
        "spinner_parsing": "Bonnetjes verwerken\u2026",
        "spinner_translating": "Artikelen verwerken\u2026",
        "warning_no_upload": "Upload minstens \u00e9\u00e9n kassabon PDF.",
        "error_no_valid": "Geen geldige kassabonnen gevonden.",
        "roommate_name": "Huisgenoot",
        "assignment_options": ["Gedeeld", "Van mij", "Huisgenoot"],
        "prev_btn": "\u2190 Vorige",
        "next_btn": "Volgende \u2192",
        "finish_btn": "Afronden",
        "receipt_counter": "Bonnetje {idx} van {total}",
        "original_receipt": "Origineel kassabon",
        "assign_all_placeholder": "Alles toewijzen\u2026",
        "all_shared": "Alles Gedeeld",
        "all_mine": "Alles Van mij",
        "all_roommate": "Alles Huisgenoot",
        "col_item": "Artikel",
        "col_final_price": "Eindprijs",
        "col_split": "Verdeling",
        "col_subtotal": "Subtotaal",
        "col_bonuses": "Bonussen",
        "col_total": "Totaal",
        "edit_bonus_title": "Bonusverdeling bewerken",
        "edit_bonus_caption": (
            "Bonussen worden automatisch verdeeld over de kortingsartikelen. "
            "Pas hieronder aan als de verdeling niet klopt."
        ),
        "owes_label": "Huisgenoot is je verschuldigd",
        "your_items_label": "Jouw artikelen",
        "roommate_items_label": "Artikelen {roommate}",
        "shared_items_label": "Gedeelde artikelen",
        "grand_total_label": "Totaalbedrag",
        "shared_half_label": "Helft van gedeelde artikelen",
        "roommate_own_label": "Eigen artikelen {roommate}",
        "owes_total_label": "{roommate} is verschuldigd",
        "download_report_btn": "Download Rapport",
        "start_over_btn": "Opnieuw beginnen",
        "receipt_details_header": "Kassabondetails",
        "deposit_label": "incl. \u20ac{amount} statiegeld",
        "saved_label": "bespaard \u20ac{amount}",
        "items_mismatch_warning": (
            "Artikeltotaal (\u20ac{items_sum:.2f}) komt niet overeen met kassabon totaal "
            "(\u20ac{receipt_total:.2f}) \u2014 verschil: \u20ac{diff:.2f}. "
            "Sommige artikelen zijn mogelijk niet correct herkend."
        ),
        "duplicate_warning": "Dubbel kassabon overgeslagen: {name}",
        "invalid_receipt_error": "{name} lijkt geen AH kassabon te zijn. Overgeslagen.",
        "report_filename": "kassabon_verdeling_rapport.pdf",
    },
    "en": {
        "app_title": "Receipt Splitter",
        "step_upload_header": "Upload AH Receipts",
        "description": """\
Upload one or more Albert Heijn store receipts and assign each item to yourself, your roommate, \
or split it as shared. The app calculates exactly what your roommate owes you and generates a \
PDF report you can send them.

**Here is what happens when you upload a receipt:**

- **Parsing:** Every item is extracted from the PDF: name, quantity, unit price, and final price.
- **Bonus card discounts:** Any bonus savings are detected and distributed across the discounted \
items so the split reflects what you actually paid.
- **Translation:** Item names are in Dutch on the receipt. The app automatically translates them \
to English so the review step is easy to read. You can also correct any translation manually.
- **Assignment:** You go through each item and mark it as Mine, your roommate's, or Shared. \
Shared items get split 50/50. You can also bulk-assign all items at once.
- **Summary and report:** The app totals everything up and tells you exactly how much your \
roommate owes you. You can download a full PDF breakdown to share with them.

---

**This only works with the PDF receipts from the Albert Heijn app.** These receipts are only \
available if you scanned your groceries with your Albert Heijn bonus card at checkout.

To get the PDF:

1. Open the Albert Heijn app and tap the person icon in the top right.
2. Go to **Purchases and orders**, then **Store receipts**.
3. Tap on a receipt.
4. Tap the three dots in the top right corner, then choose **Share receipt**.
5. Save or send yourself the PDF file.
""",
        "file_uploader_label": "Drop your Albert Heijn receipt PDFs here",
        "process_button": "Process Receipts",
        "spinner_parsing": "Parsing receipts\u2026",
        "spinner_translating": "Translating items & matching bonuses\u2026",
        "warning_no_upload": "Please upload at least one receipt PDF first.",
        "error_no_valid": "No valid receipts found.",
        "roommate_name": "Roommate",
        "assignment_options": ["Shared", "Mine", "Roommate"],
        "prev_btn": "\u2190 Prev",
        "next_btn": "Next \u2192",
        "finish_btn": "Finish",
        "receipt_counter": "Receipt {idx} of {total}",
        "original_receipt": "Original Receipt",
        "edit_names_btn": "Edit Names",
        "done_editing_btn": "Done Editing",
        "assign_all_placeholder": "Assign all\u2026",
        "all_shared": "All Shared",
        "all_mine": "All Mine",
        "all_roommate": "All Roommate",
        "col_item": "Item",
        "col_final_price": "Final Price",
        "col_split": "Split",
        "col_subtotal": "Subtotal",
        "col_bonuses": "Bonuses",
        "col_total": "Total",
        "edit_bonus_title": "Edit Bonus Splits",
        "edit_bonus_caption": (
            "Bonuses are automatically distributed across discounted items. "
            "Override below if the split doesn't look right."
        ),
        "owes_label": "owes you",
        "your_items_label": "Your items",
        "roommate_items_label": "{roommate}\u2019s items",
        "shared_items_label": "Shared items",
        "grand_total_label": "Grand total",
        "shared_half_label": "Half of shared items",
        "roommate_own_label": "{roommate}\u2019s own items",
        "owes_total_label": "{roommate} owes you",
        "download_report_btn": "Download Split Report",
        "start_over_btn": "Start Over",
        "receipt_details_header": "Receipt Details",
        "deposit_label": "incl. \u20ac{amount} deposit",
        "saved_label": "saved \u20ac{amount}",
        "items_mismatch_warning": (
            "Parsed items total (\u20ac{items_sum:.2f}) doesn\u2019t match receipt total "
            "(\u20ac{receipt_total:.2f}) \u2014 difference: \u20ac{diff:.2f}. "
            "Some items may not have been parsed correctly."
        ),
        "duplicate_warning": "Duplicate receipt skipped: {name}",
        "invalid_receipt_error": "{name} does not appear to be an AH receipt. Skipping.",
        "report_filename": "grocery_split_report.pdf",
    },
}

REPORT_STRINGS: dict[str, dict[str, str]] = {
    "nl": {
        "page_title": "Kassabon Verdeling Rapport",
        "report_h1": "Kassabon Verdeling Rapport",
        "generated_label": "Gegenereerd op",
        "owes_line": "{roommate} is je verschuldigd",
        "your_items": "Jouw artikelen",
        "roommate_items": "Artikelen huisgenoot",
        "shared_items": "Gedeelde artikelen",
        "shared_half_label": "Helft van gedeelde artikelen",
        "roommate_own_label": "Eigen artikelen huisgenoot",
        "owes_total_label": "Huisgenoot is verschuldigd",
        "grand_total_label": "Totaalbedrag",
        "receipts_single": "1 kassabon",
        "receipts_plural": "{n} kassabonnen",
        "items_total": "{n} artikelen totaal",
        "col_item": "Artikel",
        "col_price": "Prijs",
        "col_assigned": "Toegewezen",
        "badge_shared": "GEDEELD",
        "badge_mine": "VAN MIJ",
        "mine_label": "Van mij",
        "shared_label": "Gedeeld",
        "saved_label": "Bespaard \u20ac{amount} met bonus",
        "deposit_label": "statiegeld \u20ac{amount}",
        "bonus_edited_label": "bonus \u20ac{bonus:.2f} (gewijzigd van \u20ac{original:.2f})",
        "bonus_label": "bonus \u20ac{amount:.2f}",
        "footer": "AH Bonnetje Verdeler",
    },
    "en": {
        "page_title": "Grocery Split Report",
        "report_h1": "Grocery Split Report",
        "generated_label": "Generated",
        "owes_line": "{roommate} owes you",
        "your_items": "Your Items",
        "roommate_items": "{roommate}\u2019s Items",
        "shared_items": "Shared Items",
        "shared_half_label": "Half of shared items",
        "roommate_own_label": "{roommate}\u2019s own items",
        "owes_total_label": "{roommate} owes you",
        "grand_total_label": "Grand Total",
        "receipts_single": "1 receipt",
        "receipts_plural": "{n} receipts",
        "items_total": "{n} items total",
        "col_item": "Item",
        "col_price": "Price",
        "col_assigned": "Assigned",
        "badge_shared": "SHARED",
        "badge_mine": "MINE",
        "mine_label": "Mine",
        "shared_label": "Shared",
        "saved_label": "Saved \u20ac{amount} with bonus",
        "deposit_label": "deposit \u20ac{amount}",
        "bonus_edited_label": "bonus \u20ac{bonus:.2f} (edited from \u20ac{original:.2f})",
        "bonus_label": "bonus \u20ac{amount:.2f}",
        "footer": "AH Receipt Splitter",
    },
}
