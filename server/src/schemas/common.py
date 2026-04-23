"""Shared enums and base types used across AAX schemas."""

from enum import StrEnum


class ContentFormat(StrEnum):
    GAMEDAY_GRAPHIC = "gameday_graphic"
    HIGHLIGHT_REEL = "highlight_reel"
    SOCIAL_POST = "social_post"
    STORY = "story"
    VIDEO_CLIP = "video_clip"


class Platform(StrEnum):
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    TIKTOK = "tiktok"
    FACEBOOK = "facebook"
    YOUTUBE = "youtube"


class Sport(StrEnum):
    BASKETBALL = "basketball"
    FOOTBALL = "football"
    SOCCER = "soccer"
    BASEBALL = "baseball"
    TRACK = "track"
    SWIMMING = "swimming"
    HOCKEY = "hockey"
    OTHER = "other"
