"""
Prompts for computer use agent to interact with HealthConnect UI.
"""

NAVIGATE_TO_PATIENT_FILES_PROMPT = """
Navigate to the patient file list in HealthConnect.

TASK - Execute steps 1-3 in exact order. STOP if any step fails.

1. Locate and click on the "Bijlage" (attachments) tab
   [VERIFY: Bijlage tab is active/highlighted]

2. Wait for the attachment list to load
   [VERIFY: List of files is visible]

3. Identify all .txt files that need processing
   [VERIFY: At least one .txt file is visible in the list]

CONSTRAINTS:
- Do NOT click any element not listed above
- Do NOT navigate away from current page
- If ANY verification fails, STOP and report which step failed

When complete, report the number of .txt files found.
"""


DOWNLOAD_FILE_PROMPT = """
Download the text file: {filename}

TASK - Execute steps 1-5 in exact order. STOP if any step fails.

1. Locate the file "{filename}" in the attachment list
   [VERIFY: File is visible in the list]

2. Click the three dots (⋮) menu next to the file
   [VERIFY: Context menu appears]

3. Select "Downloaden" (Download) from the menu
   [VERIFY: Menu item is clicked]

4. Wait for download to complete (up to 10 seconds)
   [VERIFY: Download notification or file appears]

5. Verify file exists in downloads folder
   [VERIFY: File is present]

CONSTRAINTS:
- Do NOT click any element not listed above
- Do NOT navigate away from current page
- If ANY verification fails, STOP and report which step failed
- If download takes longer than 10 seconds, report timeout

When complete, report success or failure.
"""


UPLOAD_PDF_PROMPT = """
Upload the PDF file with metadata.

TASK - Execute steps 1-12 in exact order. STOP if any step fails.

File: {pdf_path}
Logical name: {logical_name}
Summary: {summary}

1. Click "Contact bewerken" (Edit contact)
   [VERIFY: Edit mode is active]

2. Click the three dots menu (⋮) at the top
   [VERIFY: Menu opens]

3. Select "Bijlage toevoegen" (Add attachment)
   [VERIFY: Upload dialog appears]

4. Select "Specialistenbrief" from the dropdown
   [VERIFY: Dropdown shows "Specialistenbrief" selected]

5. Click "Bestand kiezen" (Choose file)
   [VERIFY: File picker opens]

6. Navigate to: {pdf_path}
7. Select the file and click "Open"
   [VERIFY: Filename appears in upload field]

8. Locate the "Logische naam" (Logical name) field
   [VERIFY: Field is visible and editable]

9. Clear existing content and type: {logical_name}
   [VERIFY: Field contains "{logical_name}"]

10. Locate the "Samenvatting" (Summary) field
    [VERIFY: Field is visible and editable]

11. Type: {summary}
    [VERIFY: Summary text is visible in field]

12. Click "Toepassen" (Apply)
    [VERIFY: Form closes or shows success indication]

CONSTRAINTS:
- Do NOT click any element not listed above
- Do NOT navigate away from current page
- Do NOT attempt creative solutions if stuck
- If ANY verification fails, STOP and report which step failed

When complete, report success or failure.
"""


FINALIZE_CONTACT_PROMPT = """
Finalize the contact with no financial processing.

TASK - Execute steps 1-4 in exact order.

1. Click "Afronden" (Finalize) button
   [VERIFY: Finalization dialog appears]

2. Locate checkbox or option for "Geen financiële afhandeling"
   (No financial processing)
   [VERIFY: Option is visible]

3. Select "Geen financiële afhandeling"
   [VERIFY: Option is checked/selected]

4. Click confirm/OK button
   [VERIFY: Contact is finalized, returned to patient view]

CRITICAL: Step 3 is MANDATORY. Never finalize without selecting
"Geen financiële afhandeling".

CONSTRAINTS:
- Do NOT proceed without selecting "Geen financiële afhandeling"
- If the option is not found, STOP and report
- If ANY verification fails, STOP and report which step failed

When complete, report success or failure.
"""


VERIFY_UPLOAD_PROMPT = """
Verify that the upload completed correctly.

TASK - Confirm upload completed correctly.

Expected values:
- Logical name: {logical_name}
- Summary: {summary}
- File type: PDF

1. Navigate to patient's "Bijlage" tab if not already there
   [VERIFY: Bijlage tab is active]

2. Locate the newly uploaded PDF file (most recent file)
   [VERIFY: PDF file is visible in the list]

3. Verify the following are visible:
   - File appears in the list
   - Logical name shows: {logical_name}
   - Summary shows: {summary}
   - File type shows: PDF

4. Take screenshot as proof of successful upload

REPORT FORMAT:
- If ALL verifications pass: "VERIFIED: Upload successful"
- If ANY verification fails: "FAILED: [specific_failure_reason]"

Do NOT proceed unless verification reports "VERIFIED".
"""


DELETE_ORIGINAL_FILE_PROMPT = """
Delete the original text file: {filename}

SAFETY CHECKS - All must pass before deletion:
1. Verification status is "VERIFIED"
2. PDF file exists in processed folder
3. Checkpoint shows upload_completed=True

TASK - Execute steps 1-4 in exact order.

1. Navigate to patient's "Bijlage" tab
   [VERIFY: Bijlage tab is active]

2. Locate the original file "{filename}"
   [VERIFY: File is visible in the list]

3. Click the three dots (⋮) menu next to the file
   [VERIFY: Context menu appears]

4. Select "Verwijderen" (Delete) from the menu
   [VERIFY: Confirmation dialog appears]

5. Confirm deletion
   [VERIFY: File is removed from the list]

CRITICAL SAFETY:
- ONLY delete if all safety checks passed
- If ANY safety check fails, STOP immediately
- If ANY verification fails, STOP and report

When complete, report success or failure.
"""


STUCK_DETECTION_PROMPT = """
You appear to be stuck in a loop. You have repeated the same action 3 times.

Last 3 actions:
{action_history}

STOP and report:
1. What you were trying to do
2. What obstacle you encountered
3. What you need to proceed (human intervention, different approach, etc.)

Do NOT continue with the same action. Do NOT attempt creative workarounds.
Report the situation clearly and wait for instructions.
"""
