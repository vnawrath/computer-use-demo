from quart import Quart, render_template, redirect, url_for

app = Quart(__name__)

# Define the slide order
SLIDES = [
    ("title", "Title"),
    ("tool_calling", "Tool Calling"),
    ("history", "Evolution"),
]


def get_navigation_urls(current_slide_id):
    current_index = next(
        (i for i, (id, _) in enumerate(SLIDES) if id == current_slide_id), None
    )

    prev_url = (
        None if current_index == 0 else url_for(f"slide_{SLIDES[current_index - 1][0]}")
    )
    next_url = (
        None
        if current_index >= len(SLIDES) - 1
        else url_for(f"slide_{SLIDES[current_index + 1][0]}")
    )

    return prev_url, next_url


@app.route("/")
async def index():
    return redirect(url_for("slide_title"))


@app.route("/slides/title")
async def slide_title():
    prev_url, next_url = get_navigation_urls("title")
    return await render_template(
        "slide_title.html",
        title="AI Computer Use",
        subtitle='How to make AI click around your computer, aka "automate everything!"',
        author="Viktor Nawrath",
        email="viktor.nawrath@profiq.com",
        prev_url=prev_url,
        next_url=next_url,
    )


@app.route("/slides/tool-calling")
async def slide_tool_calling():
    prev_url, next_url = get_navigation_urls("tool_calling")
    return await render_template(
        "slide_tool_calling.html",
        title="Tool Calling in LLMs",
        prev_url=prev_url,
        next_url=next_url,
    )


@app.route("/slides/history")
async def slide_history():
    prev_url, next_url = get_navigation_urls("history")
    return await render_template(
        "slide_history.html",
        title="Evolution of Browser/Computer Control",
        prev_url=prev_url,
        next_url=next_url,
    )


if __name__ == "__main__":
    app.run(debug=True)
