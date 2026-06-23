"""Friends graph endpoints (PRD §16, Epic 6)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.middleware.principal import require_user
from src.models import User
from src.schemas.common import (
    CreateFriendRequestBody,
    FriendPublic,
    FriendRequestListPublic,
    FriendRequestPublic,
    FriendsListPublic,
    UserSearchResponsePublic,
    UserSearchResultPublic,
)
from src.services.social import (
    SocialError,
    cancel_friend_request,
    list_friend_requests,
    list_friends,
    respond_to_friend_request,
    search_users,
    send_friend_request,
    unfriend,
)

router = APIRouter(prefix="/me/friends", tags=["friends"])


def _social_error(exc: SocialError) -> HTTPException:
    return HTTPException(
        status_code=exc.http_status,
        detail={"code": exc.code, "message": exc.message},
    )


@router.get("", response_model=FriendsListPublic)
async def get_friends(
    me: User = Depends(require_user),
    session: AsyncSession = Depends(get_db),
) -> FriendsListPublic:
    rows = await list_friends(session, me)
    return FriendsListPublic(
        friends=[
            FriendPublic(
                user_id=u.id,
                username=u.username,
                display_name=u.display_name,
                avatar_url=u.avatar_url,
                friend_since=since,
            )
            for u, since in rows
        ]
    )


@router.get("/requests", response_model=FriendRequestListPublic)
async def get_requests(
    me: User = Depends(require_user),
    session: AsyncSession = Depends(get_db),
) -> FriendRequestListPublic:
    incoming, outgoing = await list_friend_requests(session, me)
    user_ids = {r.from_user_id for r in incoming + outgoing} | {
        r.to_user_id for r in incoming + outgoing
    }
    users = await _user_map(session, list(user_ids))

    def _pub(r) -> FriendRequestPublic:
        from_u = users.get(r.from_user_id)
        to_u = users.get(r.to_user_id)
        return FriendRequestPublic(
            id=r.id,
            from_user_id=r.from_user_id,
            to_user_id=r.to_user_id,
            from_username=from_u.username if from_u else None,
            from_display_name=from_u.display_name if from_u else None,
            to_username=to_u.username if to_u else None,
            to_display_name=to_u.display_name if to_u else None,
            status=r.status.value,
            created_at=r.created_at,
            responded_at=r.responded_at,
        )

    return FriendRequestListPublic(
        incoming=[_pub(r) for r in incoming],
        outgoing=[_pub(r) for r in outgoing],
    )


@router.post("/requests", response_model=FriendRequestPublic)
async def post_request(
    payload: CreateFriendRequestBody,
    me: User = Depends(require_user),
    session: AsyncSession = Depends(get_db),
) -> FriendRequestPublic:
    try:
        request = await send_friend_request(
            session, me=me, target_username=payload.username
        )
    except SocialError as exc:
        raise _social_error(exc) from exc
    users = await _user_map(session, [request.from_user_id, request.to_user_id])
    from_u = users.get(request.from_user_id)
    to_u = users.get(request.to_user_id)
    return FriendRequestPublic(
        id=request.id,
        from_user_id=request.from_user_id,
        to_user_id=request.to_user_id,
        from_username=from_u.username if from_u else None,
        from_display_name=from_u.display_name if from_u else None,
        to_username=to_u.username if to_u else None,
        to_display_name=to_u.display_name if to_u else None,
        status=request.status.value,
        created_at=request.created_at,
        responded_at=request.responded_at,
    )


@router.post("/requests/{request_id}/accept", response_model=FriendRequestPublic)
async def accept_request(
    request_id: uuid.UUID,
    me: User = Depends(require_user),
    session: AsyncSession = Depends(get_db),
) -> FriendRequestPublic:
    try:
        request = await respond_to_friend_request(
            session, me=me, request_id=request_id, accept=True
        )
    except SocialError as exc:
        raise _social_error(exc) from exc
    return await _request_to_public(session, request)


@router.post("/requests/{request_id}/decline", response_model=FriendRequestPublic)
async def decline_request(
    request_id: uuid.UUID,
    me: User = Depends(require_user),
    session: AsyncSession = Depends(get_db),
) -> FriendRequestPublic:
    try:
        request = await respond_to_friend_request(
            session, me=me, request_id=request_id, accept=False
        )
    except SocialError as exc:
        raise _social_error(exc) from exc
    return await _request_to_public(session, request)


@router.delete("/requests/{request_id}", response_model=FriendRequestPublic)
async def cancel_request(
    request_id: uuid.UUID,
    me: User = Depends(require_user),
    session: AsyncSession = Depends(get_db),
) -> FriendRequestPublic:
    try:
        request = await cancel_friend_request(
            session, me=me, request_id=request_id
        )
    except SocialError as exc:
        raise _social_error(exc) from exc
    return await _request_to_public(session, request)


@router.delete("/{other_user_id}", status_code=204)
async def delete_friend(
    other_user_id: uuid.UUID,
    me: User = Depends(require_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    try:
        await unfriend(session, me=me, other_user_id=other_user_id)
    except SocialError as exc:
        raise _social_error(exc) from exc


# ---- Search lives at /users/search but groups well here -----------------

users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.get("/search", response_model=UserSearchResponsePublic)
async def search(
    q: str = Query(..., min_length=1, max_length=64),
    limit: int = Query(default=10, ge=1, le=25),
    me: User = Depends(require_user),
    session: AsyncSession = Depends(get_db),
) -> UserSearchResponsePublic:
    results = await search_users(session, me, q, limit=limit)
    return UserSearchResponsePublic(
        results=[
            UserSearchResultPublic(
                id=u.id,
                username=u.username,
                display_name=u.display_name,
                avatar_url=u.avatar_url,
                relationship=rel,
            )
            for u, rel in results
        ]
    )


async def _user_map(
    session: AsyncSession, ids: list[uuid.UUID]
) -> dict[uuid.UUID, User]:
    if not ids:
        return {}
    from sqlalchemy import select

    result = await session.execute(select(User).where(User.id.in_(ids)))
    return {u.id: u for u in result.scalars()}


async def _request_to_public(session, request) -> FriendRequestPublic:
    users = await _user_map(session, [request.from_user_id, request.to_user_id])
    from_u = users.get(request.from_user_id)
    to_u = users.get(request.to_user_id)
    return FriendRequestPublic(
        id=request.id,
        from_user_id=request.from_user_id,
        to_user_id=request.to_user_id,
        from_username=from_u.username if from_u else None,
        from_display_name=from_u.display_name if from_u else None,
        to_username=to_u.username if to_u else None,
        to_display_name=to_u.display_name if to_u else None,
        status=request.status.value,
        created_at=request.created_at,
        responded_at=request.responded_at,
    )
