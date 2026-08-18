"""Comprehensive unit and integration tests for Member C (Processing & Verification Specialist)."""

from backend.processing.ad_blocker import AdBlocker
from backend.processing.cleaner import process_raw_html
from backend.processing.dom_cleaner import DOMCleaner
from backend.processing.entity_extractor import EntityExtractor
from backend.processing.exceptions import (
    DOMCleaningError,
    EntityExtractionError,
    MarkdownConversionError,
    ProcessingError,
    VerificationError,
)
from backend.processing.markdown_converter import MarkdownConverter
from backend.processing.verifier import verify_cross_source
from shared.schemas import FinalReport, ProcessedPage


def test_ad_blocker_detection_and_stripping() -> None:
    """Verifies that AdBlocker removes ad tags, cookie banners, and promotional wrappers."""
    blocker = AdBlocker()

    sample_html = """
    <div>
        <ins class="adsbygoogle" style="display:block"></ins>
        <div class="cookie-banner-popup">Please accept cookies to proceed.</div>
        <div class="main-content">
            <h1>Product Title</h1>
            <p>Real product description.</p>
        </div>
        <aside class="sponsored-product-listing">Sponsored ad item</aside>
    </div>
    """

    cleaned = blocker.strip_ad_tags(sample_html)
    assert "adsbygoogle" not in cleaned
    assert "cookie-banner" not in cleaned
    assert "sponsored-product" not in cleaned
    assert "Product Title" in cleaned
    assert "Real product description." in cleaned


def test_dom_cleaner_removes_scripts_and_styles() -> None:
    """Verifies that DOMCleaner strips scripts, styles, metadata, and normalizes text."""
    cleaner = DOMCleaner()

    raw_html = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Test Page</title>
            <style>body { color: red; }</style>
            <script>console.log("tracking");</script>
        </head>
        <body>
            <!-- This is a comment -->
            <svg><path d="M10 10"/></svg>
            <div id="content" style="color: blue;" onclick="alert(1)">
                <h1>Kindle Paperwhite</h1>
                <p>Features 16GB storage and 6.8 inch display.</p>
            </div>
            <noscript>JavaScript is required.</noscript>
        </body>
    </html>
    """

    cleaned = cleaner.clean_html(raw_html)
    assert "<script>" not in cleaned
    assert "<style>" not in cleaned
    assert "<svg>" not in cleaned
    assert "<!--" not in cleaned
    assert "onclick=" not in cleaned
    assert "Kindle Paperwhite" in cleaned
    assert "Features 16GB storage" in cleaned


def test_markdown_converter_semantics() -> None:
    """Verifies that MarkdownConverter preserves headings, lists, tables, and links."""
    converter = MarkdownConverter()

    sample_html = """
    <h1>Kindle Paperwhite (16GB)</h1>
    <p>The best e-reader for book lovers.</p>
    <ul>
        <li>Waterproof design</li>
        <li>Adjustable warm light</li>
        <li>10 weeks battery life</li>
    </ul>
    <table>
        <tr><th>Feature</th><th>Value</th></tr>
        <tr><td>Storage</td><td>16GB</td></tr>
        <tr><td>Price</td><td>$149.99</td></tr>
    </table>
    <p>Buy now at <a href="https://example.com/buy">Official Store</a>.</p>
    """

    markdown = converter.convert(sample_html)
    assert "# Kindle Paperwhite (16GB)" in markdown
    assert "* Waterproof design" in markdown
    assert "| Feature | Value |" in markdown
    assert "| Storage | 16GB |" in markdown
    assert "[Official Store](https://example.com/buy)" in markdown


def test_entity_extractor_attributes() -> None:
    """Verifies that EntityExtractor accurately identifies prices, stock status, and SKUs."""
    extractor = EntityExtractor()

    markdown_sample = """
    # Kindle Paperwhite 16GB (Latest Gen)

    * Price: $149.99
    * In Stock: Yes, ready to ship
    * SKU: 6522295
    * Model Number: B09TWDYSVP
    * Rating: 4.7 out of 5 stars

    ### Technical Specs
    | Storage | 16GB |
    | Color | Black |
    """

    entities = extractor.extract_entities(markdown_sample)
    assert entities["price"] == "$149.99"
    assert entities["availability"] == "In Stock"
    assert "B09TWDYSVP" in entities["model_number"] or "6522295" in entities["model_number"]
    assert "4.7 / 5" in entities["rating"]
    assert entities.get("storage") == "16GB"


def test_entity_extractor_targeted_keys() -> None:
    """Verifies that EntityExtractor respects targeted extraction_keys."""
    extractor = EntityExtractor()

    markdown_sample = """
    Price: $199.00
    Availability: In Stock
    SKU: ABC-9988
    Weight: 200g
    """

    entities = extractor.extract_entities(markdown_sample, target_keys=["price", "sku"])
    assert "price" in entities
    assert "sku" in entities or "model_number" in entities


def test_page_processor_pipeline_integration() -> None:
    """Verifies end-to-end Stage 3 execution returning a valid ProcessedPage schema object."""
    raw_html = """
    <html>
        <body>
            <script>alert("ad");</script>
            <div id="product-overview">
                <h1>Kindle Paperwhite</h1>
                <p class="price-box">Price: $149.99</p>
                <p>Status: In Stock</p>
                <p>Model: B09TWDYSVP</p>
            </div>
        </body>
    </html>
    """

    processed: ProcessedPage = process_raw_html(
        raw_html=raw_html,
        step_id=1,
        domain="amazon.com",
    )

    assert isinstance(processed, ProcessedPage)
    assert processed.step_id == 1
    assert processed.source_domain == "amazon.com"
    assert "Kindle Paperwhite" in processed.cleaned_markdown
    assert processed.entities.get("price") == "$149.99"
    assert processed.entities.get("availability") == "In Stock"


def test_verification_engine_consensus() -> None:
    """Verifies that agreeing sources produce confidence = 1.0 and clean comparison table."""
    page_1 = ProcessedPage(
        step_id=1,
        source_domain="amazon.com",
        cleaned_markdown="Kindle Paperwhite $149.99 In Stock",
        entities={"price": "$149.99", "availability": "In Stock", "model_number": "B09TWDYSVP"},
    )
    page_2 = ProcessedPage(
        step_id=2,
        source_domain="bestbuy.com",
        cleaned_markdown="Kindle Paperwhite $149.99 In Stock",
        entities={"price": "$149.99", "availability": "In Stock", "model_number": "B09TWDYSVP"},
    )

    report: FinalReport = verify_cross_source(
        pages=[page_1, page_2],
        goal_id="goal_test_123",
    )

    assert isinstance(report, FinalReport)
    assert report.goal_id == "goal_test_123"
    assert report.confidence_score == 1.0
    assert len(report.contradictions) == 0
    expected_page_count = 2
    assert len(report.comparison_table) == expected_page_count
    assert len(report.sources) == expected_page_count
    assert "amazon.com" in report.sources[0].domain
    assert "bestbuy.com" in report.sources[1].domain


def test_verification_engine_contradiction_detection() -> None:
    """Verifies that divergent assertions result in detected contradictions and adjusted score."""
    page_1 = ProcessedPage(
        step_id=1,
        source_domain="amazon.com",
        cleaned_markdown="Kindle $149.99 In Stock",
        entities={"price": "$149.99", "availability": "In Stock"},
    )
    page_2 = ProcessedPage(
        step_id=2,
        source_domain="target.com",
        cleaned_markdown="Kindle $169.99 In Stock",
        entities={"price": "$169.99", "availability": "In Stock"},
    )

    report: FinalReport = verify_cross_source(
        pages=[page_1, page_2],
        goal_id="goal_discrepancy_test",
    )

    assert report.confidence_score < 1.0
    assert len(report.contradictions) > 0
    assert any("price" in c.lower() for c in report.contradictions)


def test_verification_engine_single_source_and_empty() -> None:
    """Verifies graceful handling of single source and empty page lists."""
    empty_report = verify_cross_source(pages=[], goal_id="goal_empty")
    assert empty_report.confidence_score == 0.0
    assert len(empty_report.sources) == 0

    single_page = ProcessedPage(
        step_id=1,
        source_domain="wikipedia.org",
        cleaned_markdown="Article summary.",
        entities={"topic": "Web Agents"},
    )
    single_report = verify_cross_source(pages=[single_page], goal_id="goal_single")
    assert single_report.confidence_score > 0.0
    assert len(single_report.comparison_table) == 1


def test_custom_exceptions_inheritance() -> None:
    """Verifies that all domain exceptions correctly inherit from ProcessingError."""
    assert issubclass(DOMCleaningError, ProcessingError)
    assert issubclass(MarkdownConversionError, ProcessingError)
    assert issubclass(EntityExtractionError, ProcessingError)
    assert issubclass(VerificationError, ProcessingError)
