"""Explicit developer-only composition boundary; service profiles fail closed."""


def load_runtime_profile(
    mode,
    path,
    *,
    clock=None,
    fixture="two_task_read",
    configuration=None,
    inputs=None,
    herald_configuration=None,
    renderer=None,
):
    if mode != "offline":
        raise ValueError("UNSUPPORTED service profile is not qualified")
    if fixture == "surveyor_herald":
        from goldgraft_fakes.herald_profile import create_collaboration_profile

        if configuration is None or herald_configuration is None:
            raise ValueError("MISSING_EVIDENCE role configurations")
        return create_collaboration_profile(
            path,
            configuration=configuration,
            herald_configuration=herald_configuration,
            renderer=renderer,
            clock=clock,
            inputs=inputs,
        )
    if fixture == "surveyor_inventory":
        from goldgraft_fakes.surveyor_profile import create_surveyor_profile

        if configuration is None:
            raise ValueError("MISSING_EVIDENCE role configuration")
        return create_surveyor_profile(
            path, configuration=configuration, clock=clock, inputs=inputs
        )
    if fixture != "two_task_read":
        raise ValueError("UNSUPPORTED offline fixture")
    # Deferred import keeps shared foundation usable without optional offline counterparts.
    from goldgraft_fakes.plan5_profile import create_profile

    return create_profile(path, clock=clock)


def load_component_profile(mode, path, **kwargs):
    if mode != "offline":
        raise ValueError("UNSUPPORTED unqualified real component profile")
    from goldgraft_fakes.component_profile import create_component_profile

    return create_component_profile(path, **kwargs)
