"""Versioned synthetic text-inference policy and conservative standard-rate accounting."""

from dataclasses import asdict, dataclass

from goldgraft_contracts.plan5_common import content_digest


@dataclass(frozen=True)
class Profile:
    model: str = "claude-haiku-5-5"
    sdk: str = "2.7.0"
    input_cap: int = 24000
    output_cap: int = 1536
    max_turns: int = 4
    timeout_seconds: int = 90
    input_micro_per_million: int = 100000
    output_micro_per_million: int = 500000
    framing_token_allowance: int = 1024
    purpose: str = "original_synthetic_MIT_agent_component_evaluation_only"

    @property
    def ref(self):
        return "local:model-profile:" + content_digest(asdict(self))

    def cost(self, inputs, outputs):
        if any(type(n) is not int or n < 0 for n in [inputs, outputs]):
            raise ValueError("INVALID usage")
        return (
            inputs * self.input_micro_per_million + outputs * self.output_micro_per_million + 999999
        ) // 1000000

    @property
    def turn_reservation(self):
        return self.cost(self.input_cap, self.output_cap)

    @property
    def batch_reservation(self):
        return self.turn_reservation * self.max_turns


@dataclass(frozen=True)
class SonnetProfile(Profile):
    """Separately qualified comparison profile; the Haiku Profile ref is unchanged.

    Claude Sonnet 5.5 rejects disabled thinking (HTTP400); between_tools is its
    lowest setting (no extended thinking). Standard rates $2/$10 per MTok.
    """

    model: str = "claude-sonnet-5-5"
    output_cap: int = 4000
    max_turns: int = 8
    input_micro_per_million: int = 2000000
    output_micro_per_million: int = 10000000
    thinking_type: str = "between_tools"
    # Ceiling profile: the provider count (observed exact on 163/163 responses)
    # bounds input instead of bytes; reservation still assumes the full 24k cap.
    input_bound: str = "provider_count"
    count_margin_tokens: int = 512
    # Prompt caching of the fixed tools+system prefix (5-minute TTL). Writes are
    # 1.25x and reads 0.05x base input on Sonnet 5.5 (pricing page, 11 Nov2026).
    cache_prefix: bool = True
    cache_write_micro_per_million: int = 2500000
    cache_read_micro_per_million: int = 100000

    def cost_cached(self, uncached, created, read, outputs):
        if any(type(n) is not int or n < 0 for n in [uncached, created, read, outputs]):
            raise ValueError("INVALID usage")
        return (
            uncached * self.input_micro_per_million
            + created * self.cache_write_micro_per_million
            + read * self.cache_read_micro_per_million
            + outputs * self.output_micro_per_million
            + 999999
        ) // 1000000

    @property
    def turn_reservation(self):
        # Worst case: every input token billed as a cache write.
        return self.cost_cached(0, self.input_cap, 0, self.output_cap)


@dataclass(frozen=True)
class HaikuLongProfile(Profile):
    """Additive Haiku profile for multi-step component flows (e.g. Builder's 5 calls need
    4 turns at best, Haiku's whole cap). Same model and prices; the Haiku Profile ref is
    unchanged, so existing qualifications stay valid."""

    max_turns: int = 8


PROFILES = {"haiku": Profile, "sonnet": SonnetProfile, "haiku8": HaikuLongProfile}


def route_profile(files):
    """Pick the model before dispatch from package shape, never after a failure.

    Haiku is proven only when every first-wave read fits one response (files+2<=4);
    larger packages need the Sonnet ceiling profile, which keeps <=4 calls/response.
    """
    return "haiku" if len(files) + 2 <= 4 else "sonnet"
