import openai
import asyncio
import logging
import json5
import json
import os
from typing import Dict, Any, List

logger = logging.getLogger("orchestrator")

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            openai.api_key = self.api_key
        else:
            logger.warning("OPENAI_API_KEY not found. Automated classification will use fallback rules.")

    async def analyze_content(self, text: str, competitors: List[Dict] = None) -> Dict[str, Any]:
        """
        Analyzes the text using OpenAI to extract structured data and classification.
        If a competitor list is provided, the LLM will also identify which competitor
        the document is about and return the matched competitor ID.
        """
        default_result = {
            "summary": "Analysis unavailable.",
            "therapeutic_area": "General",
            "category": "General",
            "impact_level": "Low",
            "relevance_score": 3.0,
            "entities": {
                "company": "N/A",
                "drug": "N/A",
                "phase": "N/A",
                "indication": "N/A"
            },
            "matched_competitor_id": None,
            "tags": []
        }

        if not self.api_key:
            return default_result

        truncated_text = text[:4000]
        loop = asyncio.get_running_loop()

        # Build competitor context for the prompt
        competitor_context = ""
        if competitors:
            comp_list = []
            for c in competitors:
                comp_list.append(f"  - ID: {c['id']}, Name: {c['name']}")
            competitor_context = (
                "\n\nYou are provided with the following list of KNOWN COMPETITORS being tracked. "
                "If the document mentions any of these companies (even by abbreviation, subsidiary, or alternate name), "
                "return their exact ID in the 'matched_competitor_id' field. "
                "If no competitor matches, return null.\n\n"
                "COMPETITOR LIST:\n" + "\n".join(comp_list)
            )

        try:
            response = await loop.run_in_executor(
                None,
                lambda: openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an expert Medical and Competitor Intelligence Analyst. "
                                "Analyze the following medical news or clinical trial text. "
                                "Extract structured data and classify its importance for a pharmaceutical competitive intelligence dashboard. "
                                "Return JSON only."
                                + competitor_context +
                                "\n\nSchema:"
                                "{"
                                '  "summary": "Concise executive summary (1-2 sentences).", '
                                '  "therapeutic_area": "Primary Therapeutic Area (e.g. Oncology, Cardiovascular, Respiratory, Immunology, Neurology, etc.)", '
                                '  "category": "One of: Clinical Trial, Regulatory, Competitor Intelligence, General", '
                                '  "impact_level": "High (Major trial results, approvals), Medium (Phase 2, filings), Low (Pre-clinical, general news)", '
                                '  "relevance_score": "A float from 0.0 to 10.0 indicating how relevant and impactful this is for competitive intelligence. 9-10: breakthrough results, major approvals. 6-8: significant trials, regulatory filings. 3-5: routine updates. 0-2: tangential news.", '
                                '  "entities": {'
                                '    "company": "Primary company name mentioned in the text (e.g. AstraZeneca, Pfizer)", '
                                '    "drug": "Drug name/code (e.g. AZD1234) or N/A", '
                                '    "phase": "Phase (e.g. Phase 3) or N/A", '
                                '    "indication": "Target disease/indication"'
                                '  }, '
                                '  "matched_competitor_id": "The ID from the COMPETITOR LIST above if the document is about one of the tracked competitors, otherwise null", '
                                '  "tags": ["list", "of", "relevant", "keywords"]'
                                "}"
                            )
                        },
                        {"role": "user", "content": truncated_text}
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
            )

            content = response.choices[0].message.content.strip()
            
            try:
                parsed_result = json5.loads(content)
                return parsed_result
            except Exception as e:
                logger.error(f"Error parsing JSON from OpenAI: {e}. Content: {content}")
                return default_result

        except Exception as e:
            logger.error(f"LLM analysis error: {e}")
            return default_result
