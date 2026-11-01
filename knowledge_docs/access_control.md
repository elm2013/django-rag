# Access control

A web application should distinguish authentication from authorization.

Authentication verifies who the user is. Authorization determines what an
authenticated user is allowed to do.

In Django REST Framework, permissions can be checked before a view handler
runs. A project may also define domain-specific policies for viewing or
editing resources.

A useful design keeps policy evaluation separate from HTTP request parsing.
The API layer should validate the request, while an application service
coordinates the use case and a policy component makes access decisions.
