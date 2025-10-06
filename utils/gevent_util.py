# Copyright Flexday Solutions LLC, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# See file LICENSE.txt for full license details.

"""
This module provides a utility function `gevent_spawn` for asynchronously executing 
a func in a Gevent greenlet and handling the result. It is designed to streamline 
the process of spawning greenlets to make HTTP requests or execute other asynchronous 
tasks that can be performed concurrently.
The `gevent_spawn` function allows you to pass any func (any callable)
along with its required positional and keyword arguments, which will then be executed 
within a greenlet. The function waits for the greenlet to finish and either returns 
the result or raises any exceptions that occurred during execution.
This module is particularly useful in scenarios where multiple HTTP requests or
I/O-bound tasks need to be performed concurrently, improving the overall performance
of an application by utilizing Gevent's cooperative multitasking.
"""


import gevent
from typing import Dict, Any, Callable, List


def gevent_spawn(
    func: Callable[..., Any],
    *args: Any,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Constructs and spawns a greenlet for making an HTTP request.
    Args:
        func (Callable[..., Any]): The func to be spawned in the greenlet.
        *args (Any): Positional arguments to pass to the func.
        **kwargs (Any): Keyword arguments to pass to the func.
        
    Returns:
        Dict[str, Any]: A dictionary containing the result of the HTTP request.
    """
    # Spawn a greenlet with the provided func, args, and kwargs
    greenlet = gevent.spawn(func, *args, **kwargs)

    # Wait for the greenlet to finish
    greenlet.join()

    # Check if the greenlet threw an exception
    if greenlet.exception:
        raise greenlet.exception
    else:
        # Retrieve the response if no exception occurred
        response = greenlet.value

    return response