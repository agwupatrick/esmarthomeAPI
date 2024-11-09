from uuid import uuid4,UUID

def generate_invite_link(team_id: UUID, base_url: str = "http://localhost:5173/invite") -> str:
    """
    Generate a unique invite link for the team based on team ID.
    """
    unique_token = uuid4()
    invite_link = f"{base_url}/{team_id}/{unique_token}"  # Construct the invite URL
    return invite_link
