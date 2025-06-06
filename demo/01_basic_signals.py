"""Basic Datastar signals demo - minimal example"""

from starhtml import *

app, rt = star_app(
    title="Basic Signals Demo"
)

@rt('/')
def home():
    return Div(
        H1("Basic Datastar Signals"),
        
        Div(
            Button("Increment", ds_on_click="$counter++"),
            Button("Decrement", ds_on_click="$counter--"),
            Button("Reset", ds_on_click="$counter = 0"),
            
            P("Counter: ", ds_text="$counter", style="font-size: 24px; margin: 20px 0;"),
            
            ds_signals={"counter": 0}
        ),
        
        style="padding: 20px; max-width: 400px; margin: 0 auto; text-align: center;"
    )

if __name__ == "__main__":
    print("Basic Signals Demo running on http://localhost:5001")
    serve()