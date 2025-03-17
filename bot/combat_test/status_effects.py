"""Defines all the status effects that a spell can have"""

from random import randint

class Status:
    """A Status base class object"""
    def __init__(self, status, caster: str, power: int, chance: int, duration: int):
        self.caster = caster
        self.status = status
        self.power = power
        self.chance = chance
        self.duration = duration
        self.max_duration = duration


    def apply_status(self, target) -> str:
        """Applies a status effect object on the player"""
        roll = randint(1, 100)
        if roll < self.chance:
            new_status = type(self)(self.caster, self.power,
                                    self.chance, self.duration)
            target.status_effects.append(new_status)
        return f"{target.user.display_name} is now affected by {self.status}!" if roll < self.chance else f"{target.user.display_name} resisted {self.status}."


    def reduce_status(self, target) -> str:
        """Reduces status duration each turn"""
        if self.duration > 0:
            self.duration -= 1
        if self.duration == 0:
            target.status_effects.remove(self)
            self.duration = self.max_duration
            return f"{self.status} effect on {target.user.display_name} has worn off."
        return f"Duration {self.duration} turns on {self.status}"

    def change_targets(self, player, targets):
        """Default: Does nothing, override in subclasses if needed"""
        return [player] + targets



# Specific Status Effect Classes
class Paralyze(Status):
    """A Paralysis object, that allows the player to skip a targets turn"""
    def __init__(self, caster, power, chance, duration):
        super().__init__("Paralyze", caster, power, chance, duration)

    def apply_status(self, target):
        message = super().apply_status(target)
        target.can_move = False  # Prevents movement
        return message

    def reduce_status(self, target):
        message = super().reduce_status(target)
        if self.duration == 0:
            target.can_move = True  # Restore movement
        return message

    def change_targets(self, player, targets):
        return []


class Frozen(Status):
    """Slows a targets speed"""
    def __init__(self, caster, power, chance, duration):
        super().__init__("Frozen", caster, power, chance, duration)

    def apply_status(self, target):
        message = super().apply_status(target)
        target.speed -= self.power  # Example: Reduce speed
        return message

    def reduce_status(self, target):
        message = super().reduce_status(target)
        if self.duration == 0:
            target.speed = target.data.get('speed')  # Restore speed
        return message


class Burning(Status):
    """Burns the target for some damage over a duration"""
    def __init__(self, caster, power, chance, duration):
        super().__init__("Burning", caster, power, chance, duration)

    def reduce_status(self, target):
        damage = self.power/self.duration
        target.health -= damage
        message = super().reduce_status(target)
        return f"{target.user.display_name} takes {damage} burn damage!\n{message}" if message else f"{target.user.display_name} takes {damage} burn damage!"


class Poisoned(Status):
    """Poisons the target for a percentage of health for a duration"""
    def __init__(self, caster, power, chance, duration):
        super().__init__("Poisoned", caster, power, chance, duration)

    def reduce_status(self, target):
        damage = target.health * (self.power / 100)  # Power% of HP
        target.health -= damage
        message = super().reduce_status(target)
        return f"{target.user.display_name} suffers {damage} poison damage!\n{message}" if message else f"{target.user.display_name} suffers {damage} poison damage!"


class Charmed(Status):
    """Charms the target so they can't attack the target"""
    def __init__(self, caster, power, chance, duration):
        super().__init__("Charmed", caster, power, chance, duration)

    def apply_status(self, target):
        message = super().apply_status(target)
        target.cannot_attack_caster = True
        return message

    def reduce_status(self, target):
        message = super().reduce_status(target)
        if self.duration == 0:
            target.cannot_attack_caster = False
        return message

    def change_targets(self, player, targets):
        if self.caster in targets:
            targets.remove(self.caster)
        return targets


class Regenerating(Status):
    """The target heals a percentage of power"""
    def __init__(self, caster, power, chance, duration):
        super().__init__("Regenerating", caster, power, chance, duration)

    def reduce_status(self, target):
        heal = target.max_health * (self.power/100)  # 5% of max HP
        target.health += heal
        target.health = min(target.health, target.max_health)
        message = super().reduce_status(target)
        return f"{target.user.display_name} regenerates {heal} HP!\n{message}" if message else f"{target.user.display_name} regenerates {heal} HP!"


class Blessed(Status):
    """The target removes all status effects"""
    def __init__(self, caster, power, chance, duration):
        super().__init__("Blessed", caster, power, chance, duration)

    def apply_status(self, target):
        target.status_effects.clear()
        return f"{target.user.display_name} is cleansed of all status effects!"



class Confusion(Status):
    """The Target can't see the mana cost for their spells"""
    def __init__(self, caster, power, chance, duration):
        super().__init__("Confusion", caster, power, chance, duration)

    def apply_status(self, target):
        message = super().apply_status(target)
        target.mana_hidden = True
        return message

    def reduce_status(self, target):
        message = super().reduce_status(target)
        if self.duration == 0:
            target.mana_hidden = False
        return message


class ManaBoost(Status):
    """The max mana the target has is boosted"""
    def __init__(self, caster, power, chance, duration):
        super().__init__("Mana Boost", caster, power, chance, duration)
        self.boost_amount = 1 + (power / 100)  # Scale increase by power
        self.regen_amount = 1 + (power / 200)  # Regenerate half the boost

    def apply_status(self, target):
        target.max_mana *= self.boost_amount
        target.mana *= self.regen_amount
        return f"{target.user.display_name}'s max mana increased by {round((self.boost_amount - 1) * 100, 2)}%!"


class HealthBoost(Status):
    """The max health of the target is boosted"""
    def __init__(self, caster, power, chance, duration):
        super().__init__("Health Boost", caster, power, chance, duration)
        self.boost_amount = 1 + (power / 100)  # Scale increase by power
        self.regen_amount = 1+ (power / 200)  # Regenerate half the boost


def apply_status(self, target):
    """Applies the health boost effect"""
    target.max_health *= self.boost_amount
    target.health *= self.boost_amount
    return f"{target.user.display_name}'s max health increased by {round((self.boost_amount - 1) * 100, 2)}%!"



class ExtremeSpeed(Status):
    """Massively increases the targets speed"""
    def __init__(self, caster, power, chance, duration):
        super().__init__("Extreme Speed", caster, power, chance, duration)

    def apply_status(self, target):
        target.speed += self.power  # Example: Increase speed
        return f"{target.user.display_name} moves at extreme speed!"


class Armor(Status):
    """Increases the targets defense"""
    def __init__(self, caster, power, chance, duration):
        super().__init__("Armor", caster, power, chance, duration)

    def apply_status(self, target):
        target.defense *= 1 + (self.power / 100)
        return f"{target.user.display_name} gains {round(((self.power / 100) - 1) * 100, 2)} extra defense!"


class Taunt(Status):
    """The target can only target the caster"""
    def __init__(self, caster, power, chance, duration):
        super().__init__("Taunt", caster, power, chance, duration)

    def change_targets(self, player, targets):
        return [self.caster]


class Leech(Status):
    """The target looses some health a turn and the caster gains that health"""
    def __init__(self, caster, power, chance, duration):
        super().__init__("Leech", caster, power, chance, duration)

    def apply_status(self, target):
        message = super().apply_status(target)
        target.leech_active = True
        return message

    def reduce_status(self, target):
        damage = target.max_health * (self.power / 100) # 4% HP loss
        target.health -= damage
        self.caster.health += damage
        message = super().reduce_status(target)
        return f"{target.user.display_name} loses {damage} HP due to leech!\n{message}" if message else f"{target.user.display_name} loses {damage} HP due to leech!"

# Weaknesses as specific subclasses

class ElementalWeakness(Status):
    """Sets a players elemental weakness"""
    def __init__(self, element: str):
        super().__init__(f"{element} Weakness", chance=100, duration=3)
        self.element = element

    def apply_status(self, target):
        target.weaknesses.append(self.element)
        return f"{target.user.display_name} is now weak to {self.element}!"

class FireWeakness(ElementalWeakness):
    """A fire weakness"""
    def __init__(self):
        super().__init__("Fire")


class WaterWeakness(ElementalWeakness):
    """A water weakness"""
    def __init__(self):
        super().__init__("Water")


class EarthWeakness(ElementalWeakness):
    """A Earth Weakness"""
    def __init__(self):
        super().__init__("Earth")


class AirWeakness(ElementalWeakness):
    """A Air weakness"""
    def __init__(self):
        super().__init__("Air")
