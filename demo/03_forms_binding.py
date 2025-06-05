"""Forms and binding demo - shows input binding and form handling"""

from starhtml import star_app, Div, Button, P, H1, Input, Form, Label
from starhtml.datastar import ds_signals, ds_on, ds_text, ds_bind, ds_show
from starhtml.core import serve

app, rt = star_app(
    title="Forms and Binding Demo"
)

@rt('/')
def home():
    return Div(
        H1("Forms and Binding Demo"),
        
        Div(
            Form(
                Label("Name:", style="display: block; margin: 10px 0 5px;"),
                Input(type="text", placeholder="Enter your name", **ds_bind("name"), style="width: 100%; padding: 8px;"),
                
                Label("Email:", style="display: block; margin: 10px 0 5px;"),
                Input(type="email", placeholder="Enter your email", **ds_bind("email"), style="width: 100%; padding: 8px;"),
                
                Label("Age:", style="display: block; margin: 10px 0 5px;"),
                Input(type="number", **ds_bind("age"), style="width: 100%; padding: 8px;"),
                
                Div(
                    Button("Submit", type="button", 
                           **ds_on(click="$submitted = true; $name = ''; $email = ''; $age = ''; setTimeout(() => $submitted = false, 2000)"), 
                           style="margin-right: 10px; padding: 10px 20px;"),
                    Button("Clear", type="button", 
                           **ds_on(click="$name = ''; $email = ''; $age = ''; $submitted = false"), 
                           style="padding: 10px 20px;"),
                    style="margin-top: 15px;"
                ),
                
                style="margin: 20px 0; padding: 20px; border: 1px solid #ddd;"
            ),
            
            # Live preview
            Div(
                H1("Live Preview:"),
                P("Name: ", **ds_text("$name || 'Not entered'")),
                P("Email: ", **ds_text("$email || 'Not entered'")),
                P("Age: ", **ds_text("$age || 'Not entered'")),
                
                # Show when form is submitted
                Div(
                    P("✓ Form submitted successfully!", style="color: green; font-weight: bold;"),
                    **ds_show("$submitted")
                ),
                
                style="margin: 20px 0; padding: 20px; background: #f8f8f8;"
            ),
            
            **ds_signals(name="", email="", age="", submitted=False)
        ),
        
        style="padding: 20px; max-width: 600px; margin: 0 auto;"
    )

if __name__ == "__main__":
    print("Forms and Binding Demo running on http://localhost:5001")
    serve()