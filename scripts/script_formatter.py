def format_story(post):

    title = post["title"]
    story = post["story"]

    script = f"""
Reddit user asks:
{title}
Here's what happened.
{story}
"""

    return script