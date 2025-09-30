# Datastar Docs

**All documentation on a single page for offline reading and LLM ingestion.**

*   [Guide](#guide)
    *   [Getting Started](#getting-started)
    *   [Reactive Signals](#reactive-signals)
    *   [Datastar Expressions](#datastar-expressions)
    *   [Backend Requests](#backend-requests)
*   [Reference](#reference)
    *   [Attributes](#attributes)
    *   [Actions](#actions)    
    *   [SSE Events](#sse-events)
    *   [Security](#security)

<a id="guide"></a>
# Guide

<a id="getting-started"></a>
# Getting Started

Datastar simplifies frontend development – allowing you to build backend-driven, interactive UIs using a **hypermedia-first** approach.

> Hypermedia refers to linked content like images, audio, and video – an extension of hypertext (the “H” in HTML and HTTP).

Datastar offers backend-driven reactivity like [htmx](https://htmx.org/) and frontend-driven reactivity like [Alpine.js](https://alpinejs.dev/) in a lightweight framework that doesn’t need any npm packages or other dependencies. It provides two major functions:

1.  Modify the DOM and state by sending events from your backend.
2.  Build reactivity into your frontend using HTML attributes.

<a id="data-*"></a>
## `data-*`

At the core of Datastar are [data-*](https://developer.mozilla.org/en-US/docs/Web/HTML/How_to/Use_data_attributes) attributes (hence the name). They allow you to add reactivity to your frontend and interact with your backend in a declarative way.


The [`data-on`](#data-on) attribute can be used to attach an event listener to an element and execute an expression whenever the event is triggered. The value of the attribute is a [Datastar expression](#datastar-expressions) in which JavaScript can be used.

```html
<button data-on-click="alert('I’m sorry, Dave. I’m afraid I can’t do that.')">
    Open the pod bay doors, HAL.
</button>
```

We’ll explore more data attributes in the [next section of the guide](#reactive-signals).

<a id="patching-elements"></a>
## Patching Elements

With Datastar, the backend *drives* the frontend by **patching** (adding, updating and removing) HTML elements in the DOM.

Datastar receives elements from the backend and manipulates the DOM using a morphing strategy (by default). Morphing ensures that only modified parts of the DOM are updated, preserving state and improving performance.

Datastar provides [actions](#backend-actions) for sending requests to the backend. The [`@get()`](#get) action sends a `GET` request to the provided URL using a browser native [fetch](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API).

```html
<button data-on-click="@get('/endpoint')">
    Open the pod bay doors, HAL.
</button>
<div id="hal"></div>
```

> Actions in Datastar are helper functions that have the syntax `@actionName()`. Read more about actions in the [reference](#actions).

The backend can respond with HTML elements that will be morphed into the existing DOM:

```html
<div id="hal">
    I'm sorry, Dave. I'm afraid I can't do that.
</div>
```

In the example above, the DOM must contain an element with a `hal` ID in order for morphing to work. The backend can also send Server-Sent Events (SSE) to patch multiple elements or send updates over time.

> For detailed information about response types, patching strategies, and SSE event syntax, see the [Response Handling](#response-handling) and [SSE Events](#sse-events) sections in the reference.

<a id="reactive-signals"></a>
# Reactive Signals

In a hypermedia approach, the backend drives state to the frontend and acts as the primary source of truth. It’s up to the backend to determine what actions the user can take next by patching appropriate elements in the DOM.

Sometimes, however, you may need access to frontend state that’s driven by user interactions. Click, input and keydown events are some of the more common user events that you’ll want your frontend to be able to react to.

Datastar uses *signals* to manage frontend state. You can think of signals as reactive variables that automatically track and propagate changes in and to [Datastar expressions](#datastar-expressions). Signals are denoted using the `$` prefix.

<a id="data-attributes"></a>
## Data Attributes

Datastar allows you to add reactivity to your frontend and interact with your backend in a declarative way using [data-*](https://developer.mozilla.org/en-US/docs/Web/HTML/How_to/Use_data_attributes) attributes.


<a id="frontend-reactivity"></a>
## Frontend Reactivity

Datastar’s data attributes enable declarative signals and expressions, providing a simple yet powerful way to add reactivity to the frontend.

Datastar expressions are strings that are evaluated by Datastar [attributes](/reference/attributes) and [actions](/reference/actions). While they are similar to JavaScript, there are some important differences that are explained in the [next section of the guide](/guide/datastar_expressions).

```html
<div data-signals-hal="'...'">
    <button data-on-click="$hal = 'Affirmative, Dave. I read you.'">
        HAL, do you read me?
    </button>
    <div data-text="$hal"></div>
</div>
```

```html
<div
    data-signals="{response: '', answer: 'bread'}"
    data-computed-correct="$response.toLowerCase() == $answer"
>
    <div id="question">What do you put in a toaster?</div>
    <button data-on-click="$response = prompt('Answer:') ?? ''">BUZZ</button>
    <div data-show="$response != ''">
        You answered “<span data-text="$response"></span>”.
        <span data-show="$correct">That is correct ✅</span>
        <span data-show="!$correct">
        The correct answer is “
        <span data-text="$answer"></span>
        ” 🤷
        </span>
    </div>
</div>
```

<a id="patching-signals"></a>
## Patching Signals

Remember that in a hypermedia approach, the backend drives state to the frontend. Just like with elements, frontend signals can be **patched** (added, updated and removed) from the backend using [backend actions](#backend-actions).

```html
<div data-signals-hal="'...'">
    <button data-on-click="@get('/endpoint')">
        HAL, do you read me?
    </button>
    <div data-text="$hal"></div>
</div>
```

The backend can respond with JSON to patch signal values:

```json
{"hal": "Affirmative, Dave. I read you."}
```

Signals are merged into the frontend using [JSON Merge Patch RFC 7396](https://datatracker.ietf.org/doc/rfc7396/). The backend can also use Server-Sent Events to update signals over time.

> For detailed information about response types and SSE events for signals, see the [Response Handling](#response-handling) and [SSE Events](#sse-events) sections in the reference.

<a id="datastar-expressions"></a>
# Datastar Expressions

Datastar expressions are strings that are evaluated by `data-*` attributes. While they are similar to JavaScript, there are some important differences that make them more powerful for declarative hypermedia applications.

## Datastar Expressions

The following example outputs `1` because we’ve defined `foo` as a signal with the initial value `1`, and are using `$foo` in a `data-*` attribute.

```html
<div data-signals-foo="1">
    <div data-text="$foo"></div>
</div>
```

A variable `el` is available in every Datastar expression, representing the element that the attribute is attached to.

```html
<div id="foo" data-text="el.id"></div>
```

When Datastar evaluates the expression `$foo`, it first converts it to the signal value, and then evaluates that expression in a sandboxed context. This means that JavaScript can be used in Datastar expressions.

```html
<div data-text="$foo.length"></div>
```

JavaScript operators are also available in Datastar expressions. This includes (but is not limited to) the ternary operator `?:`, the logical OR operator `||`, and the logical AND operator `&&`. These operators are helpful in keeping Datastar expressions terse.

```html
// Output one of two values, depending on the truthiness of a signal
<div data-text="$landingGearRetracted ? 'Ready' : 'Waiting'"></div>

// Show a countdown if the signal is truthy or the time remaining is less than 10 seconds
<div data-show="$landingGearRetracted || $timeRemaining < 10">
    Countdown
</div>

// Only send a request if the signal is truthy
<button data-on-click="$landingGearRetracted && @post('/launch')">
    Launch
</button>
```

Multiple statements can be used in a single expression by separating them with a semicolon.

```html
<div data-signals-foo="1">
    <button data-on-click="$landingGearRetracted = true; @post('/launch')">
        Force launch
    </button>
</div>
```

Expressions may span multiple lines, but a semicolon must be used to separate statements. Unlike JavaScript, line breaks alone are not sufficient to separate statements.

```html
<div data-signals-foo="1">
    <button data-on-click="
        $landingGearRetracted = true; 
        @post('/launch')
    ">
        Force launch
    </button>
</div>
```

## Using JavaScript

Most of your JavaScript logic should go in `data-*` attributes, since reactive signals and actions only work in [Datastar expressions](#datastar-expressions).

> Caution: if you find yourself trying to do too much in Datastar expressions, **you are probably overcomplicating it™**.

Any additional JavaScript functionality you require that cannot belong in `data-*` attributes should be extracted out into [external scripts](#external-scripts) or, better yet, [web components](#web-components).

> Always encapsulate state and send **props down, events up**.

<a id="external-scripts"></a>
### External Scripts

When using external scripts, pass data into functions via arguments and return a result *or* listen for custom events dispatched from them **props down, events up**.

In this way, the function is encapsulated – all it knows is that it receives input via an argument, acts on it, and optionally returns a result or dispatches a custom event – and `data-*` attributes can be used to drive reactivity.

```html
<div data-signals-result>
    <input data-bind-foo 
        data-on-input="$result = myfunction($foo)"
    >
    <span data-text="$result"></span>
</div>
```

```javascript
function myfunction(data) {
    return `You entered: ${data}`;
}
```

If your function call is asynchronous then it will need to dispatch a custom event containing the result. While asynchronous code *can* be placed within Datastar expressions, Datastar will *not* await it.

```html
<div data-signals-result>
    <input data-bind-foo 
           data-on-input="myfunction(el, $foo)"
           data-on-mycustomevent__window="$result = evt.detail.value"
    >
    <span data-text="$result"></span>
</div>
```

```javascript
async function myfunction(element, data) {
    const value = await new Promise((resolve) => {
        setTimeout(() => resolve(`You entered: ${data}`), 1000;
    });
    element.dispatchEvent(
        new CustomEvent('mycustomevent', {detail: {value}})
    );
}
```

See the [sortable example](/examples/sortable).

<a id="web-components"></a>
### Web Components

[Web components](https://developer.mozilla.org/en-US/docs/Web/API/Web_components) allow you create reusable, encapsulated, custom elements. They are native to the web and require no external libraries or frameworks. Web components unlock [custom elements](https://developer.mozilla.org/en-US/docs/Web/API/Web_components/Using_custom_elements) – HTML tags with custom behavior and styling.

When using web components, pass data into them via attributes and listen for custom events dispatched from them (*props down, events up*).

In this way, the web component is encapsulated – all it knows is that it receives input via an attribute, acts on it, and optionally dispatches a custom event containing the result – and `data-*` attributes can be used to drive reactivity.

```html
<div data-signals-result="''">
    <input data-bind-foo />
    <my-component
        data-attr-src="$foo"
        data-on-mycustomevent="$result = evt.detail.value"
    ></my-component>
    <span data-text="$result"></span>
</div>
```

```javascript
class MyComponent extends HTMLElement {
    static get observedAttributes() {
        return ['src'];
    }

    attributeChangedCallback(name, oldValue, newValue) {
        const value = `You entered: ${newValue}`;
        this.dispatchEvent(
            new CustomEvent('mycustomevent', {detail: {value}})
        );
    }
}

customElements.define('my-component', MyComponent);
```

Since the `value` attribute is allowed on web components, it is also possible to use `data-bind` to bind a signal to the web component’s value. Note that a `change` event must be dispatched so that the event listener used by `data-bind` is triggered by the value change.

See the [web component example](/examples/web_component).

<a id="executing-scripts"></a>
## Executing Scripts

Just like elements and signals, the backend can also send JavaScript to be executed on the frontend using [backend actions](#backend-actions).

```html
<button data-on-click="@get('/endpoint')">
    What are you talking about, HAL?
</button>```

The backend can respond with JavaScript code that will be executed in the browser:

```javascript
alert('This mission is too important for me to allow you to jeopardize it.')
```

> For detailed information about executing scripts via different response types, see the [Response Handling](#response-handling) section in the reference.

<a id="backend-requests"></a>
# Backend Requests

Between [attributes](#attributes) and [actions](#actions), Datastar provides you with everything you need to build hypermedia-driven applications. Using this approach, the backend drives state to the frontend and acts as the single source of truth, determining what actions the user can take next.

<a id="sending-signals"></a>
## Sending Signals

By default, all signals (except for local signals whose keys begin with an underscore) are sent in an object with every backend request. When using a `GET` request, the signals are sent as a `datastar` query parameter, otherwise they are sent as a JSON body.

By sending **all** signals in every request, the backend has full access to the frontend state. This is by design. It is **not** recommended to send partial signals, but if you must, you can use the [`filterSignals`](#filterSignals) option to filter the signals sent to the backend.

<a id="nesting-signals"></a>
### Nesting Signals

Signals can be nested, making it easier to target signals in a more granular way on the backend.

Using dot-notation:

```html
<div data-signals-foo.bar="1"></div>
```

Using object syntax:

```html
<div data-signals="{foo: {bar: 1}}"></div>
```

Using two-way binding:

```html
<input data-bind-foo.bar />
```

A practical use-case of nested signals is when you have repetition of state on a page. The following example tracks the open/closed state of a menu on both desktop and mobile devices, and the [`toggleAll()`](#toggleall) action to toggle the state of all menus at once.

```html
<div data-signals="{menu: {isOpen: {desktop: false, mobile: false}}}">
    <button data-on-click="@toggleAll({include: /^menu\.isOpen\./})">
        Open/close menu
    </button>
</div>
```

<a id="reading-signals"></a>
## Reading Signals

To read signals from the backend, JSON decode the `datastar` query param for `GET` requests, and the request body for all other methods.


<a id="sse-events-1"></a>
## SSE Events

Datastar can stream [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events) (SSE) from the web server to the browser. SSE allows sending multiple events in a single response, enabling real-time updates and complex interactions.

Here's an example that combines backend-driven state with frontend interactivity:

```html
<div
    data-signals="{response: '', answer: ''}"
    data-computed-correct="$response.toLowerCase() == $answer"
>
    <div id="question"></div>
    <button data-on-click="@get('/actions/quiz')">Fetch a question</button>
    <button
        data-show="$answer != ''"
        data-on-click="$response = prompt('Answer:') ?? ''"
    >
        BUZZ
    </button>
    <div data-show="$response != ''">
        You answered “<span data-text="$response"></span>”.
        <span data-show="$correct">That is correct ✅</span>
        <span data-show="!$correct">
        The correct answer is “<span data-text="$answer"></span>” 🤷
        </span>
    </div>
</div>
```

Now when the `Fetch a question` button is clicked, the server will respond with an event to modify the `question` element in the DOM and an event to modify the `response` and `answer` signals. We’re driving state from the backend!

## Backend Actions

Datastar provides backend actions for all HTTP methods. For example, here's how to send data to the server using a `POST` request:

```html
<button data-on-click="@post('/actions/quiz')">
    Submit answer
</button>
```

> For complete documentation of all backend actions (`@get()`, `@post()`, `@put()`, `@patch()`, `@delete()`) and their options, see the [Backend Actions](#backend-actions) section in the reference.

<a id="reference"></a>
# Reference

<a id="attributes"></a>
# Attributes

Data attributes have special [casing](#attribute-casing) rules, can be [aliased](#aliasing-attributes) to avoid conflicts with other libraries, can contain [Datastar expressions](#datastar-expressions-1), and have [runtime error handling](#error-handling).


<a id="data-attr"></a>
### `data-attr`

Sets the value of any HTML attribute to an expression, and keeps it in sync.

```html
<div data-attr-title="$foo"></div>
```

The `data-attr` attribute can also be used to set the values of multiple attributes on an element using a set of key-value pairs, where the keys represent attribute names and the values represent expressions.

```html
<div data-attr="{title: $foo, disabled: $bar}"></div>
```

<a id="data-bind"></a>
### `data-bind`

Creates a signal (if one doesn’t already exist) and sets up two-way data binding between it and an element’s value. This means that the value of the element is updated when the signal changes, and the signal is updated when the value of the element changes.

The `data-bind` attribute can be placed on any HTML element on which data can be input or choices selected from (`input`, `select`,`textarea` elements, and web components). Event listeners are added for `change`, `input` and `keydown` events.

```html
<input data-bind-foo />
```

The signal name can be specified in the key (as above), or in the value (as below). This can be useful depending on the templating language you are using.

```html
<input data-bind="foo" />
```

The initial value of the signal is set to the value of the element, unless a signal has already been defined. So in the example below, `$foo` is set to `bar`.

```html
<input data-bind-foo value="bar" />
```

Whereas in the example below, `$foo` inherits the value `baz` of the predefined signal.

```html
<div data-signals-foo="baz">
    <input data-bind-foo value="bar" />
</div>
```

Multiple input values can be assigned to a single signal by predefining the signal as an array. So in the example below, `$foo` is set to `['bar', 'baz']` when both checkboxes are checked.

```html
<div data-signals-foo="[]">
    <input data-bind-foo type="checkbox" value="bar" />
    <input data-bind-foo type="checkbox" value="baz" />
</div>
```

#### Modifiers

Modifiers allow you to modify behavior when binding signals.

*   `__case` – Converts the casing of the signal name.
    *   `.camel` – Camel case: `mySignal` (default)
    *   `.kebab` – Kebab case: `my-signal`
    *   `.snake` – Snake case: `my_signal`
    *   `.pascal` – Pascal case: `MySignal`

```html
<input data-bind-my-signal__case.kebab />
```

<a id="data-class"></a>
### `data-class`

Adds or removes a class to or from an element based on an expression.

```html
<div data-class-hidden="$foo"></div>
```

If the expression evaluates to `true`, the `hidden` class is added to the element; otherwise, it is removed.

The `data-class` attribute can also be used to add or remove multiple classes from an element using a set of key-value pairs, where the keys represent class names and the values represent expressions.

```html
<div data-class="{hidden: $foo, 'font-bold': $bar}"></div>
```

#### Modifiers

Modifiers allow you to modify behavior when defining a class name.

*   `__case` – Converts the casing of the class.
    *   `.camel` – Camel case: `myClass`
    *   `.kebab` – Kebab case: `my-class` (default)
    *   `.snake` – Snake case: `my_class`
    *   `.pascal` – Pascal case: `MyClass`

```html
<div data-class-my-class__case.camel="$foo"></div>
```

<a id="data-computed"></a>
### `data-computed`

Creates a signal that is computed based on an expression. The computed signal is read-only, and its value is automatically updated when any signals in the expression are updated.

```html
<div data-computed-foo="$bar + $baz"></div>
```

Computed signals are useful for memoizing expressions containing other signals. Their values can be used in other expressions.

```html
<div data-computed-foo="$bar + $baz"></div>
<div data-text="$foo"></div>
```

> Computed signals must not be used for performing actions (changing other signals, actions, JavaScript functions, etc.). If you need to perform an action in response to a signal change, use the [`data-effect`](#data-effect) attribute.

#### Modifiers

Modifiers allow you to modify behavior when defining computed signals.

*   `__case` – Converts the casing of the signal name.
    *   `.camel` – Camel case: `mySignal` (default)
    *   `.kebab` – Kebab case: `my-signal`
    *   `.snake` – Snake case: `my_signal`
    *   `.pascal` – Pascal case: `MySignal`

```html
<div data-computed-my-signal__case.kebab="$bar + $baz"></div>
```

<a id="data-effect"></a>
### `data-effect`

Executes an expression on page load and whenever any signals in the expression change. This is useful for performing side effects, such as updating other signals, making requests to the backend, or manipulating the DOM.

```html
<div data-effect="$foo = $bar + $baz"></div>
```

<a id="data-ignore"></a>
### `data-ignore`

Datastar walks the entire DOM and applies plugins to each element it encounters. It’s possible to tell Datastar to ignore an element and its descendants by placing a `data-ignore` attribute on it. This can be useful for preventing naming conflicts with third-party libraries, or when you are unable to [escape user input](#escape-user-input).

```html
<div data-ignore data-show-thirdpartylib="">
    <div>
        Datastar will not process this element.
    </div>
</div>
```

#### Modifiers

*   `__self` – Only ignore the element itself, not its descendants.

<a id="data-ignore-morph"></a>
### `data-ignore-morph`

Similar to the `data-ignore` attribute, the `data-ignore-morph` attribute tells the `PatchElements` watcher to skip processing an element and its children when morphing elements.

```html
<div data-ignore-morph>
    This element will not be morphed.
</div>
```

> To remove the `data-ignore-morph` attribute from an element, simply patch the element with the `data-ignore-morph` attribute removed.

<a id="data-indicator"></a>
### `data-indicator`

Creates a signal and sets its value to `true` while an SSE request is in flight, otherwise `false`. The signal can be used to show a loading indicator.

```html
<button data-on-click="@get('/endpoint')"
        data-indicator-fetching
></button>
```

This can be useful for showing a loading spinner, disabling a button, etc.

```html
<button data-on-click="@get('/endpoint')"
        data-indicator-fetching
        data-attr-disabled="$fetching"
></button>
<div data-show="$fetching">Loading...</div>
```

The signal name can be specified in the key (as above), or in the value (as below). This can be useful depending on the templating language you are using.

```html
<button data-indicator="fetching"></button>
```

#### Modifiers

Modifiers allow you to modify behavior when defining indicator signals.

*   `__case` – Converts the casing of the signal name.
    *   `.camel` – Camel case: `mySignal` (default)
    *   `.kebab` – Kebab case: `my-signal`
    *   `.snake` – Snake case: `my_signal`
    *   `.pascal` – Pascal case: `MySignal`

<a id="data-json-signals"></a>
### `data-json-signals`

Sets the text content of an element to a reactive JSON stringified version of signals. Useful when troubleshooting an issue.

```html
<!-- Display all signals -->
<pre data-json-signals></pre>
```

You can optionally provide a filter object to include or exclude specific signals using regular expressions.

```html
<!-- Only show signals that include "user" in their path -->
<pre data-json-signals="{include: /user/}"></pre>

<!-- Show all signals except those ending with "temp" -->
<pre data-json-signals="{exclude: /temp$/}"></pre>

<!-- Combine include and exclude filters -->
<pre data-json-signals="{include: /^app/, exclude: /password/}"></pre>
```

#### Modifiers

Modifiers allow you to modify the output format.

*   `__terse` – Outputs a more compact JSON format without extra whitespace. Useful for displaying filtered data inline.

```html
<!-- Display filtered signals in a compact format -->
<pre data-json-signals__terse="{include: /counter/}"></pre>
```

<a id="data-on"></a>
### `data-on`

Attaches an event listener to an element, executing an expression whenever the event is triggered.

```html
<button data-on-click="$foo = ''">Reset</button>
```

An `evt` variable that represents the event object is available in the expression.

```html
<div data-on-myevent="$foo = evt.detail"></div>
```

The `data-on` attribute works with [events](https://developer.mozilla.org/en-US/docs/Web/Events) and [custom events](https://developer.mozilla.org/en-US/docs/Web/Events/Creating_and_triggering_events). The `data-on-submit` event listener prevents the default submission behavior of forms.

> Events listeners are only triggered when the event is [trusted](https://developer.mozilla.org/en-US/docs/Web/API/Event/isTrusted). This behavior can be bypassed using the `__trusted` modifier.

#### Modifiers

Modifiers allow you to modify behavior when events are triggered. Some modifiers have tags to further modify the behavior.

*   `__once` * – Only trigger the event listener once.
*   `__passive` * – Do not call `preventDefault` on the event listener.
*   `__capture` * – Use a capture event listener.
*   `__case` – Converts the casing of the event.
    *   `.camel` – Camel case: `myEvent`
    *   `.kebab` – Kebab case: `my-event` (default)
    *   `.snake` – Snake case: `my_event`
    *   `.pascal` – Pascal case: `MyEvent`
*   `__delay` – Delay the event listener.
    *   `.500ms` – Delay for 500 milliseconds (accepts any integer).
    *   `.1s` – Delay for 1 second (accepts any integer).
*   `__debounce` – Debounce the event listener.
    *   `.500ms` – Debounce for 500 milliseconds (accepts any integer).
    *   `.1s` – Debounce for 1 second (accepts any integer).
    *   `.leading` – Debounce with leading edge.
    *   `.notrail` – Debounce without trailing edge.
*   `__throttle` – Throttle the event listener.
    *   `.500ms` – Throttle for 500 milliseconds (accepts any integer).
    *   `.1s` – Throttle for 1 second (accepts any integer).
    *   `.noleading` – Throttle without leading edge.
    *   `.trail` – Throttle with trailing edge.
*   `__viewtransition` – Wraps the expression in `document.startViewTransition()` when the View Transition API is available.
*   `__window` – Attaches the event listener to the `window` element.
*   `__outside` – Triggers when the event is outside the element.
*   `__prevent` – Calls `preventDefault` on the event listener.
*   `__stop` – Calls `stopPropagation` on the event listener.
*   `__trusted` – Runs the expression even if the [`isTrusted`](https://developer.mozilla.org/en-US/docs/Web/API/Event/isTrusted) property on the event is `false`.

_* Only works with built-in events._

```html
<button data-on-click__window__debounce.500ms.leading="$foo = ''"></button>
<div data-on-my-event__case.camel__trusted="$foo = ''"></div>
```

<a id="data-on-intersect"></a>
### `data-on-intersect`

Runs an expression when the element intersects with the viewport.

```html
<div data-on-intersect="$intersected = true"></div>
```

#### Modifiers

Modifiers allow you to modify the element intersection behavior and the timing of the event listener.

*   `__once` – Only triggers the event once.
*   `__half` – Triggers when half of the element is visible.
*   `__full` – Triggers when the full element is visible.
*   `__delay` – Delay the event listener.
    *   `.500ms` – Delay for 500 milliseconds (accepts any integer).
    *   `.1s` – Delay for 1 second (accepts any integer).
*   `__debounce` – Debounce the event listener.
    *   `.500ms` – Debounce for 500 milliseconds (accepts any integer).
    *   `.1s` – Debounce for 1 second (accepts any integer).
    *   `.leading` – Debounce with leading edge.
    *   `.notrail` – Debounce without trailing edge.
*   `__throttle` – Throttle the event listener.
    *   `.500ms` – Throttle for 500 milliseconds (accepts any integer).
    *   `.1s` – Throttle for 1 second (accepts any integer).
    *   `.noleading` – Throttle without leading edge.
    *   `.trail` – Throttle with trailing edge.
*   `__viewtransition` – Wraps the expression in `document.startViewTransition()` when the View Transition API is available.

```html
<div data-on-intersect__once__full="$fullyIntersected = true"></div>
```

<a id="data-on-interval"></a>
### `data-on-interval`

Runs an expression at a regular interval. The interval duration defaults to one second and can be modified using the `__duration` modifier.

```html
<div data-on-interval="$count++"></div>
```

#### Modifiers

Modifiers allow you to modify the interval duration.

*   `__duration` – Sets the interval duration.
    *   `.500ms` – Interval duration of 500 milliseconds (accepts any integer).
    *   `.1s` – Interval duration of 1 second (default).
    *   `.leading` – Execute the first interval immediately.
*   `__viewtransition` – Wraps the expression in `document.startViewTransition()` when the View Transition API is available.

```html
<div data-on-interval__duration.500ms="$count++"></div>
```

<a id="data-on-load"></a>
### `data-on-load`

Runs an expression when the element is loaded into the DOM.

```html
<div data-on-load="$count = 1"></div>
```

#### Modifiers

Modifiers allow you to add a delay to the event listener.

*   `__delay` – Delay the event listener.
    *   `.500ms` – Delay for 500 milliseconds (accepts any integer).
    *   `.1s` – Delay for 1 second (accepts any integer).
*   `__viewtransition` – Wraps the expression in `document.startViewTransition()` when the View Transition API is available.

```html
<div data-on-load__delay.500ms="$count = 1"></div>
```

<a id="data-on-signal-patch"></a>
### `data-on-signal-patch`

Runs an expression whenever one or more signals are patched. This is useful for tracking changes, updating computed values, or triggering side effects when data updates.

```html
<div data-on-signal-patch="console.log('A signal changed!')"></div>
```

The `patch` variable is available in the expression and contains the signal patch details.

```html
<div data-on-signal-patch="console.log('Signal patch:', patch)"></div>
```

You can filter which signals to watch using the [`data-on-signal-patch-filter`](#data-on-signal-patch-filter) attribute.

#### Modifiers

Modifiers allow you to modify the timing of the event listener.

*   `__delay` – Delay the event listener.
    *   `.500ms` – Delay for 500 milliseconds (accepts any integer).
    *   `.1s` – Delay for 1 second (accepts any integer).
*   `__debounce` – Debounce the event listener.
    *   `.500ms` – Debounce for 500 milliseconds (accepts any integer).
    *   `.1s` – Debounce for 1 second (accepts any integer).
    *   `.leading` – Debounce with leading edge.
    *   `.notrail` – Debounce without trailing edge.
*   `__throttle` – Throttle the event listener.
    *   `.500ms` – Throttle for 500 milliseconds (accepts any integer).
    *   `.1s` – Throttle for 1 second (accepts any integer).
    *   `.noleading` – Throttle without leading edge.
    *   `.trail` – Throttle with trailing edge.

```html
<div data-on-signal-patch__debounce.500ms="doSomething()"></div>
```

<a id="data-on-signal-patch-filter"></a>
### `data-on-signal-patch-filter`

Filters which signals to watch when using the [`data-on-signal-patch`](#data-on-signal-patch) attribute.

The `data-on-signal-patch-filter` attribute accepts an object with `include` and/or `exclude` properties that are regular expressions.

```html
<!-- Only react to counter signal changes -->
<div data-on-signal-patch-filter="{include: /^counter$/}"></div>

<!-- React to all changes except those ending with "changes" -->
<div data-on-signal-patch-filter="{exclude: /changes$/}"></div>

<!-- Combine include and exclude filters -->
<div data-on-signal-patch-filter="{include: /user/, exclude: /password/}"></div>
```

<a id="data-preserve-attr"></a>
### `data-preserve-attr`

Preserves the value of an attribute when morphing DOM elements.

```html
<details open data-preserve-attr="open">
    <summary>Title</summary>
    Content
</details>
```

You can preserve multiple attributes by separating them with a space.

```html
<details open class="foo" data-preserve-attr="open class">
    <summary>Title</summary>
    Content
</details>
```

<a id="data-ref"></a>
### `data-ref`

Creates a new signal that is a reference to the element on which the data attribute is placed.

```html
<div data-ref-foo></div>
```

The signal name can be specified in the key (as above), or in the value (as below). This can be useful depending on the templating language you are using.

```html
<div data-ref="foo"></div>
```

The signal value can then be used to reference the element.

```html
$foo is a reference to a <span data-text="$foo.tagName"></span> element
```

#### Modifiers

Modifiers allow you to modify behavior when defining references.

*   `__case` – Converts the casing of the key.
    *   `.camel` – Camel case: `myKey`
    *   `.kebab` – Kebab case: `my-key` (default)
    *   `.snake` – Snake case: `my_key`
    *   `.pascal` – Pascal case: `MyKey`

```html
<div data-ref-my-signal__case.kebab></div>
```

<a id="data-show"></a>
### `data-show`

Shows or hides an element based on whether an expression evaluates to `true` or `false`. For anything with custom requirements, use [`data-class`](#data-class) instead.

```html
<div data-show="$foo"></div>
```

To prevent flickering of the element before Datastar has processed the DOM, you can add a `display: none` style to the element to hide it initially.

```html
<div data-show="$foo" style="display: none"></div>
```

<a id="data-signals"></a>
### `data-signals`

Patches (adds, updates or removes) one or more signals into the existing signals. Values defined later in the DOM tree override those defined earlier.

```html
<div data-signals-foo="1"></div>
```

Signals can be nested using dot-notation.

```html
<div data-signals-foo.bar="1"></div>
```

The `data-signals` attribute can also be used to patch multiple signals using a set of key-value pairs, where the keys represent signal names and the values represent expressions.

```html
<div data-signals="{foo: {bar: 1, baz: 2}}"></div>
```

The value above is written in JavaScript object notation, but JSON, which is a subset and which most templating languages have built-in support for, is also allowed.

Setting a signal’s value to `null` will remove the signal.

```html
<div data-signals="{foo: null}"></div>
```

Keys used in `data-signals-*` are converted to camel case, so the signal name `mySignal` must be written as `data-signals-my-signal` or `data-signals="{mySignal: 1}"`.

Signals beginning with an underscore are *not* included in requests to the backend by default. You can opt to include them by modifying the value of the [`filterSignals`](#filterSignals) option.

> Signal names cannot begin with nor contain a double underscore (`__`), due to its use as a modifier delimiter.

#### Modifiers

Modifiers allow you to modify behavior when patching signals.

*   `__case` – Converts the casing of the signal name.
    *   `.camel` – Camel case: `mySignal` (default)
    *   `.kebab` – Kebab case: `my-signal`
    *   `.snake` – Snake case: `my_signal`
    *   `.pascal` – Pascal case: `MySignal`
*   `__ifmissing` Only patches signals if their keys do not already exist. This is useful for setting defaults without overwriting existing values.

```html
<div data-signals-my-signal__case.kebab="1"
     data-signals-foo__ifmissing="1"
></div>
```

<a id="data-style"></a>
### `data-style`

Sets the value of inline CSS styles on an element based on an expression, and keeps them in sync.

```html
<div data-style-background-color="$usingRed ? 'red' : 'blue'"></div>
<div data-style-display="$hiding && 'none'"></div>
```

The `data-style` attribute can also be used to set multiple style properties on an element using a set of key-value pairs, where the keys represent CSS property names and the values represent expressions.

```html
<div data-style="{
    display: $hiding ? 'none' : 'flex',
    flexDirection: 'column',
    color: $usingRed ? 'red' : 'green'
}"></div>
```

Style properties can be specified in either camelCase (e.g., `backgroundColor`) or kebab-case (e.g., `background-color`). They will be automatically converted to the appropriate format.

Empty string, `null`, `undefined`, or `false` values will restore the original inline style value if one existed, or remove the style property if there was no initial value. This allows you to use the logical AND operator (`&&`) for conditional styles: `$condition && 'value'` will apply the style when the condition is true and restore the original value when false.

```html
<!-- When $x is false, color remains red from inline style -->
<div style="color: red;" data-style-color="$x && 'green'"></div>

<!-- When $hiding is true, display becomes none; when false, reverts to flex from inline style -->
<div style="display: flex;" data-style-display="$hiding && 'none'"></div>
```

The plugin tracks initial inline style values and restores them when data-style expressions become falsy or during cleanup. This ensures existing inline styles are preserved and only the dynamic changes are managed by Datastar.

<a id="data-text"></a>
### `data-text`

Binds the text content of an element to an expression.

```html
<div data-text="$foo"></div>
```

<a id="datastar-expressions-1"></a>
## Datastar Expressions

Datastar expressions can parse signals (prefixed with `$`). A variable `el` is available, representing the element the attribute is on.

```html
<div id="bar" data-text="$foo + el.id"></div>
```

Read more about [Datastar expressions](#datastar-expressions) in the guide.

<a id="error-handling"></a>
## Error Handling

Datastar has built-in error handling. When an attribute is used incorrectly, a descriptive error is logged to the console with a link to a context-aware error page for more information.

```
Uncaught datastar runtime error: textKeyNotAllowed
More info: https://data-star.dev/errors/runtime/text_key_not_allowed?...
Context: { ... }
```

<a id="actions"></a>
# Actions

Datastar provides actions for use in expressions.

> The `@` prefix designates actions that are safe to use. Datastar uses `Function()` constructors to execute these actions in a secure, sandboxed environment.

<a id="peek"></a>
### `@peek()`

> `@peek(callable: () => any)`

Allows accessing signals without subscribing to their changes.

```html
<div data-text="$foo + @peek(() => $bar)"></div>
```

The expression will re-evaluate when `$foo` changes, but not when `$bar` changes.

<a id="setall"></a>
### `@setAll()`

> `@setAll(value: any, filter?: {include: RegExp, exclude?: RegExp})`

Sets the value of all matching signals.

> Use the [Datastar Inspector](#datastar-inspector) to inspect and filter signals.

```html
<!-- Sets the `foo` signal only -->
<div data-signals-foo="false">
    <button data-on-click="@setAll(true, {include: /^foo$/})"></button>
</div>

<!-- Sets all signals starting with `user.` -->
<div data-signals="{user: {name: '', nickname: ''}}">
    <button data-on-click="@setAll('johnny', {include: /^user\./})"></button>
</div>
```

<a id="toggleall"></a>
### `@toggleAll()`

> `@toggleAll(filter?: {include: RegExp, exclude?: RegExp})`

Toggles the boolean value of all matching signals.

```html
<!-- Toggles all signals starting with `is` -->
<div data-signals="{isOpen: false, isActive: true, isEnabled: false}">
    <button data-on-click="@toggleAll({include: /^is/})"></button>
</div>
```

<a id="backend-actions"></a>
## Backend Actions

<a id="get"></a>
### `@get()`

> `@get(uri: string, options={})`

Sends a `GET` request using the Fetch API. The response should contain Datastar SSE events.

```html
<button data-on-click="@get('/endpoint')"></button>
```

By default, requests include a `Datastar-Request: true` header and all signals (except those prefixed with `_`) as a `datastar` query parameter. This can be changed with the `filterSignals` option.

To keep the connection open when the page is hidden, set `openWhenHidden: true`.

```html
<button data-on-click="@get('/endpoint', {openWhenHidden: true})"></button>
```

To send form-encoded requests, use `contentType: 'form'`.

```html
<button data-on-click="@get('/endpoint', {contentType: 'form'})"></button>
```

For file uploads, use `multipart/form-data` encoding on the form element. See the [form data example](/examples/form_data).

```html
<form enctype="multipart/form-data">
    <input type="file" name="file" />
    <button data-on-click="@get('/endpoint', {contentType: 'form'})"></button>
</form>
```

<a id="post"></a>
### `@post()`
> `@post(uri: string, options={})`

<a id="put"></a>
### `@put()`
> `@put(uri: string, options={})`

<a id="patch"></a>
### `@patch()`
> `@patch(uri: string, options={})`

<a id="delete"></a>
### `@delete()`
> `@delete(uri: string, options={})`

These actions work the same as `@get()` but send `POST`, `PUT`, `PATCH`, or `DELETE` requests respectively. For these methods, signals are sent as a JSON body.

<a id="options"></a>
### Options

*   <code id="contentType">contentType</code>: `'json'` or `'form'`. Defaults to `'json'`.
*   <code id="filterSignals">filterSignals</code>: An object `{include: RegExp, exclude: RegExp}` to filter signals sent with the request.
*   <code id="selector">selector</code>: A CSS selector for a form when `contentType` is `'form'`.
*   <code id="headers">headers</code>: An object of custom headers.
*   <code id="openWhenHidden">openWhenHidden</code>: `true` or `false`. Defaults to `false`.
*   <code id="retryInterval">retryInterval</code>, <code id="retryScaler">retryScaler</code>, <code id="retryMaxWaitMs">retryMaxWaitMs</code>, <code id="retryMaxCount">retryMaxCount</code>: Control retry behavior.
*   <code id="requestCancellation">requestCancellation</code>: `'auto'`, `'disabled'`, or an `AbortController`. Defaults to `'auto'`.

<a id="request-cancellation"></a>
### Request Cancellation

By default, a new request on an element cancels any existing request on the same element. This can be changed with the `requestCancellation` option.

```html
<!-- Allow concurrent requests -->
<button data-on-click="@get('/endpoint', {requestCancellation: 'disabled'})">Allow Multiple</button>

<!-- Custom abort controller -->
<div data-signals-controller="new AbortController()">
    <button data-on-click="@get('/endpoint', {requestCancellation: $controller})">Start Request</button>
    <button data-on-click="$controller.abort()">Cancel Request</button>
</div>
```

<a id="response-handling"></a>
### Response Handling

Backend actions handle different response `content-type` values:
*   `text/event-stream`: Standard SSE with Datastar events.
*   `text/html`: HTML to patch into the DOM. Can use `datastar-selector`, `datastar-mode`, and `datastar-use-view-transition` headers.
*   `application/json`: JSON signals to patch. Can use `datastar-only-if-missing` header.
*   `text/javascript`: JavaScript to execute. Can use `datastar-script-attributes` header.

<a id="text/html"></a>
#### `text/html`
When returning HTML (`text/html`), the server can optionally include the following response headers:

*   `datastar-selector` – A CSS selector for the target elements to patch
*   `datastar-mode` – How to patch the elements (`outer`, `inner`, `remove`, `replace`, `prepend`, `append`, `before`, `after`). Defaults to `outer`.
*   `datastar-use-view-transition` – Whether to use the [View Transition API](https://developer.mozilla.org/en-US/docs/Web/API/View_Transitions_API) when patching elements.

```
response.headers.set('Content-Type', 'text/html')
response.headers.set('datastar-selector', '#my-element')
response.headers.set('datastar-mode', 'inner')
response.body = '<p>New content</p>'
```

<a id="application/json"></a>
#### `application/json`
When returning JSON (`application/json`), the server can optionally include the following response header:

*   `datastar-only-if-missing` – If set to `true`, only patch signals that don't already exist.

```
response.headers.set('Content-Type', 'application/json')
response.headers.set('datastar-only-if-missing', 'true')
response.body = JSON.stringify({ foo: 'bar' })
```

<a id="text/javascript"></a>
#### `text/javascript`
When returning JavaScript (`text/javascript`), the server can optionally include the following response header:

*   `datastar-script-attributes` – Sets the script element's attributes using a JSON encoded string.

```
response.headers.set('Content-Type', 'text/javascript')
response.headers.set('datastar-script-attributes', JSON.stringify({ type: 'module' }))
response.body = 'console.log("Hello from server!");'
```

<a id="events"></a>
### Events

All backend actions trigger `datastar-fetch` events: `started`, `finished`, `error`, `retrying`, `retries-failed`.

```html
<div data-on-datastar-fetch="
    evt.detail.type === 'error' && console.log('Fetch error encountered')
"></div>
```

<a id="sse-events"></a>
# SSE Events

Responses to [backend actions](#backend-actions) with a content type of `text/event-stream` can contain zero or more Datastar [SSE](https://en.wikipedia.org/wiki/Server-sent_events) events.

<a id="event-types"></a>
## Event Types

<a id="datastar-patch-elements"></a>
### `datastar-patch-elements`

Patches one or more elements in the DOM. By default, it morphs elements by matching top-level IDs.

```
event: datastar-patch-elements
data: elements <div id="foo">Hello world!</div>
```

> Place IDs on top-level elements to be morphed and on child elements whose state you want to preserve.

See the [SVG morphing example](/examples/svg_morphing) for handling SVGs.

Additional `data` lines can override default behavior:

| Key | Description |
|---|---|
| `data: mode outer` | Morphs the outer HTML (default). |
| `data: mode inner` | Morphs the inner HTML. |
| `data: mode replace` | Replaces the outer HTML. |
| `data: mode prepend` | Prepends elements to the target’s children. |
| `data: mode append` | Appends elements to the target’s children. |
| `data: mode before` | Inserts elements before the target. |
| `data: mode after` | Inserts elements after the target. |
| `data: mode remove` | Removes the target elements. |
| `data: selector #foo`| Selects the target element using a CSS selector. |
| `data: useViewTransition true` | Use view transitions when patching. Defaults to `false`.|
| `data: elements` | The HTML elements to patch. |

<a id="datastar-patch-signals"></a>
### `datastar-patch-signals`

Patches signals into the existing signals on the page.

```
event: datastar-patch-signals
data: signals {foo: 1, bar: 2}
```

Signals can be removed by setting their value to `null`.

```
event: datastar-patch-signals
data: signals {foo: null, bar: null}
```

Sample output with non-default options:

```
event: datastar-patch-signals
data: onlyIfMissing true
data: signals {foo: 1, bar: 2}
```

<a id="security"></a>
# Security

[Datastar expressions](#datastar-expressions) are evaluated in a sandboxed context.

<a id="escape-user-input"></a>
## Escape User Input

The golden rule is to never trust user input. Always escape user input in Datastar expressions to prevent Cross-Site Scripting (XSS) attacks.

<a id="avoid-sensitive-data"></a>
## Avoid Sensitive Data

Signal values are visible in the source code and can be modified by the user. Avoid leaking sensitive data in signals and always implement backend validation.

<a id="ignore-unsafe-input"></a>
## Ignore Unsafe Input

If you cannot escape unsafe user input, use the [`data-ignore`](#data-ignore) attribute to tell Datastar to ignore the element and its descendants.

<a id="content-security-policy"></a>
## Content Security Policy

When using a [Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP) (CSP), `unsafe-eval` must be allowed for scripts, as Datastar evaluates expressions using an [IIFE](https://developer.mozilla.org/en-US/docs/Glossary/IIFE).

```html
<meta http-equiv="Content-Security-Policy" 
    content="script-src 'self' 'unsafe-eval';"
>
```