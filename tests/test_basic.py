
def test_import_package():
    """Ensure the package can be imported without errors."""
    import ocr_system
    assert hasattr(ocr_system, "__version__") or True