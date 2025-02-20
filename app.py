from quart import Quart, render_template, redirect, url_for, send_file
import io
from desktop_sandbox import DesktopManager

app = Quart(__name__)
desktop_manager = DesktopManager()

# Define the slide order
SLIDES = [
    ("title", "Title"),
    ("tool_calling", "Tool Calling"),
    ("history", "Evolution"),
    ("claude_computer", "Claude Computer Use"),
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


@app.route("/slides/claude-computer")
async def slide_claude_computer():
    prev_url, next_url = get_navigation_urls("claude_computer")
    return await render_template(
        "slide_claude_computer.html",
        title="Claude Computer Use",
        prev_url=prev_url,
        next_url=next_url,
    )


@app.route("/desktop-stream")
async def desktop_stream():
    """Endpoint to get the latest desktop screenshot"""
    screenshot = desktop_manager.take_screenshot()
    return await send_file(io.BytesIO(screenshot), mimetype="image/jpeg")


@app.before_serving
async def startup():
    """Initialize the desktop sandbox before serving"""
    global desktop_manager
    desktop_manager = DesktopManager()


@app.after_serving
async def shutdown():
    """Cleanup the desktop sandbox after serving"""
    desktop_manager.cleanup()


if __name__ == "__main__":
    app.run(debug=True)
