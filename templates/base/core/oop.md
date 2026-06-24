# Base — Object-Oriented Design

[ID: base-oop]

## SOLID principles

Apply SOLID at the class, module, and service level:

- **S — Single Responsibility**: every class or module has exactly one reason
  to change; split anything that serves more than one concern
- **O — Open/Closed**: extend behaviour by adding new code, not by modifying
  existing code; use interfaces, abstract base classes, or composition
- **L — Liskov Substitution**: subtypes must be fully substitutable for their
  base type without altering correctness; never override a method in a way
  that weakens its contract
- **I — Interface Segregation**: prefer many small, focused interfaces over
  one large general-purpose one; callers should not depend on methods they
  do not use
- **D — Dependency Inversion**: depend on abstractions, not concretions;
  inject dependencies rather than instantiating them inside a class

## OOP

- Prefer **composition over inheritance** — inherit only to model a true
  is-a relationship; compose for code reuse
- **Encapsulate** implementation details — expose behaviour through a public
  interface, hide state and implementation
- Design to interfaces (or protocols / abstract base classes), not concrete
  types
- Keep class hierarchies shallow — more than two levels of inheritance is a
  signal to refactor towards composition
- **Internal identifiers must align with their layer** — a module or class
  whose name implies a role it does not hold (an `endpoints.py` with no
  routes, a `*RestApi` class that is not the REST API) misleads readers and
  forces clarifying asides; when the layering and the name disagree, rename
  to match the layer

## Design patterns

- Apply established **GoF design patterns** where they fit the problem —
  do not invent ad-hoc solutions for problems that have named solutions
- Favour **behavioural patterns** for algorithm variation:
  Strategy, Command, Observer, Template Method
- Favour **structural patterns** for object composition:
  Adapter, Decorator, Facade, Proxy
- Use **creational patterns** to decouple object creation:
  Factory Method, Abstract Factory, Builder
- Use **Singleton** only for stateless services or infrastructure objects
  (logger, config) — never for mutable shared state
- Name the pattern in code when you use one: a class named
  `OrderExportStrategy` communicates intent; a class named `OrderHelper`
  does not

## Aspect-Oriented Programming (AOP)
[ID: base-oop-aop]

- **Do not use AOP frameworks** — hidden cross-cutting behaviour (method
  interception, bytecode weaving, runtime proxies) makes code hard to read,
  debug, and test
- Implement cross-cutting concerns explicitly:
  - Logging: call the logger directly in the function
  - Auth: explicit middleware or guard in the call chain
  - Transactions: explicit context manager or decorator with visible
    call site
  - Validation: explicit call at the boundary
- Transparent decorators (a decorator that wraps and clearly delegates) are
  acceptable; opaque interceptors that inject hidden behaviour are not
