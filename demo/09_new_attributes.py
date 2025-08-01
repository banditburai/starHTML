"""Demo of newly implemented Datastar attributes"""

from starhtml import *

app, rt = star_app(
    title="New Datastar Attributes Demo",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
    ],
)


@rt("/")
def home():
    return Div(
        H1("New Datastar Attributes Demo", cls="text-3xl font-bold mb-6"),
        # data-ignore demo
        Div(
            H2("1. data-ignore Demo", cls="text-2xl font-semibold mb-4"),
            P("The section below is ignored by Datastar (no reactivity):", cls="mb-2"),
            Div(
                P("This content is ignored", ds_text("$ignored_signal")),
                Button("Won't work", ds_on_click("$counter++")),
                ds_ignore(),
                cls="border p-4 bg-gray-100 rounded",
            ),
            P("This button outside works normally:"),
            Button("Increment", ds_on_click("$counter++"), cls="bg-blue-600 text-white px-4 py-2 rounded mt-2"),
            P("Counter: ", ds_text("$counter"), cls="mt-2"),
            cls="mb-8",
        ),
        # data-ignore-morph demo
        Div(
            H2("2. data-ignore-morph Demo", cls="text-2xl font-semibold mb-4"),
            P("Video below won't be disrupted during morphing:", cls="mb-2"),
            Video(
                Source(src="https://www.w3schools.com/html/mov_bbb.mp4", type="video/mp4"),
                ds_ignore("self"),
                controls=True,
                cls="w-full max-w-md",
            ),
            Button(
                "Update page (video keeps playing)",
                ds_on_click("$update_time = new Date().toLocaleTimeString()"),
                cls="bg-green-600 text-white px-4 py-2 rounded mt-2",
            ),
            P("Last update: ", ds_text("$update_time"), cls="mt-2"),
            cls="mb-8",
        ),
        # data-on-load demo
        Div(
            H2("3. data-on-load Demo", cls="text-2xl font-semibold mb-4"),
            P("This message loads automatically:", cls="mb-2"),
            Div(
                P(
                    "Loading...",
                    ds_text("$load_message"),
                    ds_on_load("$load_message = 'Component loaded at ' + new Date().toLocaleTimeString()"),
                ),
                cls="border p-4 bg-blue-50 rounded",
            ),
            P("With __once modifier (only loads once):", cls="mb-2 mt-4"),
            Div(
                P(
                    "Loading...",
                    ds_text("$once_message"),
                    ds_on_load("$once_message = 'Loaded once at ' + new Date().toLocaleTimeString()", "once"),
                ),
                cls="border p-4 bg-green-50 rounded",
            ),
            cls="mb-8",
        ),
        # data-preserve-attr demo
        Div(
            H2("4. data-preserve-attr Demo", cls="text-2xl font-semibold mb-4"),
            P("Form values preserved during updates:", cls="mb-2"),
            Form(
                Input(ds_preserve_attr("value"), type="text", placeholder="Type here...", cls="border p-2 rounded"),
                Textarea(
                    ds_preserve_attr("value"), placeholder="Write something...", cls="border p-2 rounded mt-2 w-full"
                ),
                Select(
                    Option("Option 1", value="1"),
                    Option("Option 2", value="2"),
                    Option("Option 3", value="3"),
                    ds_preserve_attr("value"),
                    cls="border p-2 rounded mt-2",
                ),
                cls="space-y-2",
            ),
            Button(
                "Update page (form values preserved)",
                ds_on_click("$preserve_update = new Date().toLocaleTimeString()"),
                cls="bg-purple-600 text-white px-4 py-2 rounded mt-4",
            ),
            P("Last update: ", ds_text("$preserve_update"), cls="mt-2"),
            cls="mb-8",
        ),
        # data-json-signals demo
        Div(
            H2("5. data-json-signals Demo (Debug View)", cls="text-2xl font-semibold mb-4"),
            P("All signals displayed as JSON:", cls="mb-2"),
            Pre(ds_json_signals(), cls="bg-gray-900 text-green-400 p-4 rounded font-mono text-sm overflow-auto"),
            P("Filtered signals (only those containing 'counter' or 'Time'):", cls="mb-2 mt-4"),
            Pre(
                ds_json_signals(include="(counter|Time)"),
                cls="bg-gray-900 text-blue-400 p-4 rounded font-mono text-sm overflow-auto",
            ),
            cls="mb-8",
        ),
        # Initialize signals
        ds_signals(
            counter=0,
            ignored_signal="This won't update!",
            update_time="Not updated yet",
            load_message="Loading...",
            once_message="Loading...",
            preserve_update="Not updated yet",
        ),
        cls="max-w-4xl mx-auto p-6",
    )


if __name__ == "__main__":
    serve(port=5001)
