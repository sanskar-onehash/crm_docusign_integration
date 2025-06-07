def format_pem_key(flat_key: str) -> str:
    """Restore newlines to a flat PEM RSA key."""
    flat_key = flat_key.replace("-----BEGIN RSA PRIVATE KEY-----", "")
    flat_key = flat_key.replace("-----END RSA PRIVATE KEY-----", "")
    # Remove any extra whitespace
    flat_key = (
        flat_key.replace(" ", "").replace("\t", "").replace("\r", "").replace("\n", "")
    )

    # Split into 64-character lines (standard PEM line length)
    lines = [flat_key[i : i + 64] for i in range(0, len(flat_key), 64)]

    # Reconstruct properly
    return (
        "-----BEGIN RSA PRIVATE KEY-----\n"
        + "\n".join(lines)
        + "\n-----END RSA PRIVATE KEY-----\n"
    )
