"""Cross-source verification and confidence scoring engine for Stage 4 & 5."""

import logging
import re
from typing import Any

from backend.processing.exceptions import VerificationError
from shared.schemas import FinalReport, ProcessedPage, SourceCitation


logger = logging.getLogger(__name__)


class VerificationEngine:
    """Evaluates cross-source consensus, detects contradictions, and scores data confidence."""

    def __init__(self) -> None:
        """Initializes the VerificationEngine."""
        logger.debug("VerificationEngine initialized.")

    def verify(self, pages: list[ProcessedPage], goal_id: str) -> FinalReport:
        """Cross-verifies extracted entities across multiple sources and compiles a FinalReport.

        Args:
            pages: List of ProcessedPage objects containing extracted data per step.
            goal_id: Active session transaction ID.

        Returns:
            A validated, frozen FinalReport object with synthesized facts and confidence score.

        Raises:
            VerificationError: If verification processing fails.
        """
        logger.info(
            "Starting cross-source verification for goal '%s' across %d pages.",
            goal_id,
            len(pages),
        )

        try:
            # Handle edge case: empty page list
            if not pages:
                logger.warning("No processed pages provided for verification.")
                return FinalReport(
                    goal_id=goal_id,
                    summary="No sources were successfully processed to compile findings.",
                    comparison_table=[],
                    confidence_score=0.0,
                    contradictions=["No source pages were available for verification."],
                    sources=[],
                )

            # 1. Build comparison table rows and collect citations
            comparison_table: list[dict[str, Any]] = []
            citations: list[SourceCitation] = []
            domain_entities: dict[str, dict[str, Any]] = {}

            for page in pages:
                domain = page.source_domain or "unknown.com"
                row: dict[str, Any] = {
                    "source": domain,
                    "step_id": page.step_id,
                    **page.entities,
                }
                comparison_table.append(row)
                domain_entities[domain] = page.entities

                citations.append(
                    SourceCitation(
                        domain=domain,
                        url=f"https://{domain}" if not domain.startswith("http") else domain,
                        screenshot_path=f"/artifacts/screenshots/{goal_id}_step{page.step_id}.webp",
                    )
                )

            # 2. Detect contradictions and calculate attribute consensus
            contradictions, confidence_score, consensus_facts = self._evaluate_consensus(pages)

            # 3. Synthesize human-readable executive summary
            summary = self._generate_summary(
                pages=pages,
                consensus_facts=consensus_facts,
                contradictions=contradictions,
                confidence_score=confidence_score,
            )

            report = FinalReport(
                goal_id=goal_id,
                summary=summary,
                comparison_table=comparison_table,
                confidence_score=confidence_score,
                contradictions=contradictions,
                sources=citations,
            )

            logger.info(
                "Verification complete for goal '%s'. Confidence: %.2f, Contradictions: %d.",
                goal_id,
                confidence_score,
                len(contradictions),
            )
            return report

        except Exception as e:
            logger.error("Verification engine failed: %s", str(e), exc_info=True)
            raise VerificationError(f"Cross-source verification failed: {e}") from e

    def _evaluate_consensus(
        self, pages: list[ProcessedPage]
    ) -> tuple[list[str], float, dict[str, Any]]:
        """Evaluates agreement on extracted attributes across all processed pages.

        Args:
            pages: List of ProcessedPage objects.

        Returns:
            A tuple of (contradictions_list, overall_confidence_score, consensus_facts_dict).
        """
        total_pages = len(pages)
        if total_pages <= 1:
            # Single source has no cross-verification counterpart
            single_entities = pages[0].entities if pages else {}
            return ([], 0.85 if single_entities else 0.5, single_entities)

        attribute_values = self._collect_attribute_values(pages)
        contradictions, attribute_scores, consensus_facts = self._analyze_attributes(
            attribute_values
        )

        if not attribute_scores:
            return (["No structured attributes found across consulted sources."], 0.5, {})

        overall_confidence = round(sum(attribute_scores) / len(attribute_scores), 2)
        overall_confidence = max(0.0, min(1.0, overall_confidence))
        return contradictions, overall_confidence, consensus_facts

    def _collect_attribute_values(
        self, pages: list[ProcessedPage]
    ) -> dict[str, dict[str, list[str]]]:
        """Collects and normalizes attribute values grouped by domain across all pages.

        Args:
            pages: List of ProcessedPage objects.

        Returns:
            Mapping of attribute -> normalized_value -> [domains].
        """
        attribute_values: dict[str, dict[str, list[str]]] = {}
        for page in pages:
            domain = page.source_domain
            for attr, val in page.entities.items():
                if val is None:
                    continue
                str_val = str(val).strip()
                if not str_val:
                    continue
                norm_val = self._normalize_value(attr, str_val)
                if attr not in attribute_values:
                    attribute_values[attr] = {}
                if norm_val not in attribute_values[attr]:
                    attribute_values[attr][norm_val] = []
                attribute_values[attr][norm_val].append(domain)
        return attribute_values

    def _analyze_attributes(
        self, attribute_values: dict[str, dict[str, list[str]]]
    ) -> tuple[list[str], list[float], dict[str, Any]]:
        """Analyzes attribute value maps to compute scores and detect contradictions.

        Args:
            attribute_values: Mapping of attribute -> normalized_value -> [domains].

        Returns:
            Tuple of (contradictions, per-attribute confidence scores, consensus facts).
        """
        contradictions: list[str] = []
        attribute_scores: list[float] = []
        consensus_facts: dict[str, Any] = {}

        for attr, val_map in attribute_values.items():
            total_sources = sum(len(d_list) for d_list in val_map.values())
            if total_sources == 0:
                continue

            sorted_vals = sorted(val_map.items(), key=lambda item: len(item[1]), reverse=True)
            top_val, top_domains = sorted_vals[0]
            attr_confidence = len(top_domains) / total_sources
            attribute_scores.append(attr_confidence)
            consensus_facts[attr] = top_val

            if len(val_map) > 1:
                conflict_details = [
                    f"{', '.join(domains)} asserts '{val}'" for val, domains in val_map.items()
                ]
                contradictions.append(f"Discrepancy for '{attr}': {'; '.join(conflict_details)}.")

        return contradictions, attribute_scores, consensus_facts

    def _normalize_value(self, attribute_name: str, value_str: str) -> str:
        """Normalizes attribute strings for reliable comparison.

        Args:
            attribute_name: The name of the property (e.g., 'price', 'availability').
            value_str: The raw extracted string value.

        Returns:
            Normalized comparable string.
        """
        val = value_str.strip()

        # Price normalization (e.g. "$149.99" -> "149.99")
        if "price" in attribute_name.lower() or "cost" in attribute_name.lower():
            # Extract digits and decimal point
            match = re.search(r"(\d+(?:\.\d{2})?)", val.replace(",", ""))
            if match:
                try:
                    num = float(match.group(1))
                    return f"${num:.2f}"
                except ValueError:
                    pass

        # Availability normalization
        if "availability" in attribute_name.lower() or "stock" in attribute_name.lower():
            lower_val = val.lower()
            if "in stock" in lower_val or "available" in lower_val:
                return "In Stock"
            if "out of stock" in lower_val or "unavailable" in lower_val or "sold out" in lower_val:
                return "Out of Stock"

        # Model number / SKU normalization
        if (
            "model" in attribute_name.lower()
            or "sku" in attribute_name.lower()
            or "asin" in attribute_name.lower()
        ):
            return val.upper()

        return val

    def _generate_summary(
        self,
        pages: list[ProcessedPage],
        consensus_facts: dict[str, Any],
        contradictions: list[str],
        confidence_score: float,
    ) -> str:
        """Synthesizes a clear natural language executive summary.

        Args:
            pages: List of processed page sources.
            consensus_facts: Dictionary of majority consensus facts.
            contradictions: List of flagged contradictions.
            confidence_score: Calculated confidence metric.

        Returns:
            Natural language narrative summarizing verified findings.
        """
        domains = [p.source_domain for p in pages if p.source_domain]
        unique_domains = list(dict.fromkeys(domains))
        domain_str = ", ".join(unique_domains)

        summary_parts: list[str] = [
            (
                f"Autonomous multi-source extraction completed across "
                f"{len(unique_domains)} domain(s): {domain_str}."
            )
        ]

        if consensus_facts:
            facts_str = ", ".join(
                f"{k.replace('_', ' ').capitalize()}: {v}" for k, v in consensus_facts.items()
            )
            summary_parts.append(f"Consensus findings: {facts_str}.")

        if contradictions:
            summary_parts.append(
                f"Note: {len(contradictions)} inconsistency/discrepancy detected across sources."
            )
        else:
            summary_parts.append(
                "All cross-referenced data points verified consistently across sources."
            )

        summary_parts.append(f"Overall confidence score: {int(confidence_score * 100)}%.")
        return " ".join(summary_parts)


# Singleton verification instance
_DEFAULT_VERIFIER = VerificationEngine()


def verify_cross_source(pages: list[ProcessedPage], goal_id: str) -> FinalReport:
    """Convenience function for the Orchestrator (Member A) to verify facts and output FinalReport.

    Args:
        pages: List of ProcessedPage objects collected during browser steps.
        goal_id: Active transaction ID.

    Returns:
        The validated FinalReport deliverable containing comparison tables and confidence score.
    """
    return _DEFAULT_VERIFIER.verify(pages=pages, goal_id=goal_id)
