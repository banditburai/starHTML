"""Forms and binding demo - shows input binding and form handling"""

from starhtml import *

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
                Input(type="text", placeholder="Enter your name", ds_bind="$name", style="width: 100%; padding: 8px;"),
                
                Label("Email:", style="display: block; margin: 10px 0 5px;"),
                Input(type="email", placeholder="Enter your email", ds_bind="$email", style="width: 100%; padding: 8px;"),
                
                Label("Age:", style="display: block; margin: 10px 0 5px;"),
                Input(type="number", ds_bind="$age", style="width: 100%; padding: 8px;"),
                
                Div(
                    Button("Submit", type="button", 
                           ds_on_click="$submitted = true; $name = ''; $email = ''; $age = ''; setTimeout(() => $submitted = false, 2000)", 
                           style="margin-right: 10px; padding: 10px 20px;"),
                    Button("Clear", type="button", 
                           ds_on_click="$name = ''; $email = ''; $age = ''", 
                           style="padding: 10px 20px;"),
                    style="margin-top: 20px;"
                ),
                
                style="background: #f5f5f5; padding: 20px; border-radius: 8px;"
            ),
            
            Div(
                H1("Preview", style="font-size: 20px; margin-bottom: 15px;"),
                
                Div(
                    Div(
                        Label("Name:", style="font-weight: bold; display: inline-block; width: 80px;"),
                        Span(ds_text="$name || 'Not provided'", style="color: #666;"),
                        style="margin-bottom: 8px;"
                    ),
                    Div(
                        Label("Email:", style="font-weight: bold; display: inline-block; width: 80px;"),
                        Span(ds_text="$email || 'Not provided'", style="color: #666;"),
                        style="margin-bottom: 8px;"
                    ),
                    Div(
                        Label("Age:", style="font-weight: bold; display: inline-block; width: 80px;"),
                        Span(ds_text="$age || 'Not provided'", style="color: #666;"),
                        style="margin-bottom: 8px;"
                    ),
                    style="margin-bottom: 15px;"
                ),
                
                Div(
                    P("✅ Form submitted successfully!", style="color: green; font-weight: bold; margin: 0;"),
                    ds_show="$submitted",
                    style="padding: 10px; background: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px;"
                ),
                
                style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-top: 20px; border: 1px solid #dee2e6;"
            ),
            
            ds_signals={"name": "", "email": "", "age": "", "submitted": False}
        ),
        
        style="padding: 20px; max-width: 600px; margin: 0 auto;"
    )

if __name__ == "__main__":
    print("Forms and Binding Demo running on http://localhost:5001")
    serve()