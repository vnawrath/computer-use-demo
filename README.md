# AI Computer Use Presentation

This repository contains a presentation about how Large Language Models (LLMs) can be used to control computer interfaces through natural language. The presentation demonstrates how AI can interact with computer systems by interpreting screenshots and controlling keyboard/mouse inputs, making computer interaction more intuitive and accessible.

## Running the Presentation

1. Sign up for an E2B API key at https://e2b.dev/

2. Create a `.env` file in the root directory and add your API keys:

```bash
E2B_API_KEY=your_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

3. Sync dependencies with the virtual environment:

```bash
uv sync
```

4. Run the application:

```bash
uv run app.py
```

The presentation will be available at `http://localhost:5000`

## Presentation Framework

The presentation is built with Quart (async Flask) and features a modular slide system with smooth navigation and beautiful styling.

### Features

- Modular slide system with template inheritance
- Smooth navigation between slides
- Beautiful gradient styling and modern UI
- SVG diagrams support
- Responsive design
- Async web server using Quart

### Project Structure

```
.
├── app.py              # Main application file with route definitions
├── templates/
│   ├── base.html      # Base template with common styling and layout
│   ├── slide_title.html       # Title slide template
│   └── slide_tool_calling.html # Tool calling slide template
└── README.md
```

### How It Works

#### Template System

The presentation uses Jinja2 templates with inheritance:

- `base.html`: Contains common layout, styling, and navigation
- Individual slide templates extend `base.html` and provide specific content

#### Navigation

Navigation is handled through the `SLIDES` list in `app.py`:

```python
SLIDES = [
    ("title", "Title"),
    ("tool_calling", "Tool Calling"),
]
```

Each tuple contains:

- Slide ID (used in URLs and template names)
- Display name

The `get_navigation_urls()` function automatically generates prev/next URLs based on this list.

#### Adding New Slides

To add a new slide:

1. Create a new template in `templates/` (e.g., `slide_new.html`):

```html
{% extends "base.html" %} {% block content %}
<!-- Your slide content here -->
{% endblock %}
```

2. Add a new route in `app.py`:

```python
@app.route("/slides/new-slide")
async def slide_new():
    prev_url, next_url = get_navigation_urls("new_slide")
    return await render_template(
        "slide_new.html",
        title="New Slide",
        prev_url=prev_url,
        next_url=next_url,
    )
```

3. Add the slide to the `SLIDES` list:

```python
SLIDES = [
    ("title", "Title"),
    ("tool_calling", "Tool Calling"),
    ("new_slide", "New Slide"),  # Add this line
]
```

#### Styling

The presentation uses modern CSS features:

- CSS Grid and Flexbox for layout
- CSS gradients for backgrounds
- CSS transitions for hover effects
- Responsive design principles

Custom styles can be added to individual slides using the `additional_styles` block:

```html
{% block additional_styles %} .my-custom-style { /* Your CSS here */ } {%
endblock %}
```

## License

This project is open-source and available under the MIT License.
