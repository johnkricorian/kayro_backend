from fastapi import Header, HTTPException, status

def get_current_user_id(
    x_user_id: str | None = Header(
        default=None,
        alias="X-User-ID",
    ),
) -> str:
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-User-ID header.",
        )

    normalized_user_id = x_user_id.strip()

    if not normalized_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identifier.",
        )

    return normalized_user_id
