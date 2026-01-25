"""
Prompts for metadata extraction from medical documents.
"""

EXTRACTION_PROMPT = """
Analyze this Dutch medical document and extract the following metadata.
Respond ONLY with valid JSON, no additional text.

<document>
{document_content}
</document>

Extract:
1. document_type: One of ["specialistenbrief", "patiëntbrief", "verwijsbrief", "afspraakbericht", "aanvraagformulier"]
2. specialization_code: 3-letter code based on medical specialty:
   - NEU = Neurologie
   - LON = Longarts/Pulmonologie
   - URO = Urologie
   - PSY = Psychiatrie/Psychologie
   - CAR = Cardiologie
   - DER = Dermatologie
   - GYN = Gynaecologie
   - INT = Interne geneeskunde
   - OOG = Oogheelkunde
   - ORT = Orthopedie
   - KNO = Keel-neus-oorheelkunde
   - CHI = Chirurgie
   - REU = Reumatologie
   - GER = Geriatrie
   - KIN = Kindergeneeskunde
   - MDL = Maag-darm-lever
   - RAD = Radiologie
   - ANA = Anesthesiologie
   - ONC = Oncologie
   - NEF = Nefrologie
   - HEM = Hematologie

3. specialist_name: The name of the specialist (last name only, e.g., "Stam", "van der Zijde")
4. direction: "incoming" if letter is FROM a specialist TO the practice, "outgoing" if FROM the practice
5. summary: A 2-3 line summary in Dutch focusing on:
   - Clinical status (stabiel/progressief/verbeterd)
   - Key findings or diagnoses
   - Treatment recommendations
   Maximum 150 characters.

6. logical_name: Construct as [CODE].[SpecialistName]
   - For incoming: Use specialist's name (e.g., "NEU.Stam")
   - For outgoing: Use "Huisarts" or practice name
   - For hospital letters: Use hospital name (e.g., "LON.BovenIJ")

JSON format:
{{
  "document_type": "...",
  "specialization_code": "...",
  "specialist_name": "...",
  "direction": "...",
  "summary": "...",
  "logical_name": "..."
}}
"""


VERIFICATION_PROMPT = """
I just executed: {action}
Expected result: {expected_result}

Looking at this screenshot, answer ONLY:
- "PASS" if the expected result is visible
- "FAIL: [reason]" if not

Be concise and specific.
"""
