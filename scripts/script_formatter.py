from scripts.config import log_step


def format_story(post):
    title = post["title"]
    story = post["story"]
    log_step(
        f"Preparing narration script for r/{post.get('subreddit', 'unknown')} "
        f"({len(story)} story characters)."
    )

    script = f"""
Reddit user asks:
{title}
Here's what happened.
{story}
"""

    return script
