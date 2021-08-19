import random
import pytest
from location import SubVector


def test_vector():
    # Test 10 random valid vectors which shouldn't raise exceptions
    for n in range(10):
        d = random.randint(0, 10000)
        p = random.randint(-d, d)
        a = random.randint(0, 360)
        v = SubVector(d, p, a)

    # Test vectors with z offset
    v = SubVector(555, 433, 0, z_offset=100)
    assert v.xy_projection == 444

    v = SubVector(555, 233, 0, z_offset=-100)
    assert v.xy_projection == 444

    # Test properties
    v = SubVector(555, 333, 60)
    assert isinstance(v, SubVector)
    assert v.length == 555
    assert v.z == 333
    assert v.angle == 60
    assert v.xy_projection == 444

    # Angle is measured *from* the position *to* the origin,
    # so 60 degrees should result in negative x & y
    assert v.y == -222
    assert v.x == -384

    # 45° angles should result in indentical x & y
    for n in range(10):
        d = random.randint(0, 10000)
        p = random.randint(0, d)
        a = random.choice([45, 135, 225, 315])
        v = SubVector(d, p, a)
        assert abs(v.x) == abs(v.y)

    # Some more invalid vectors
    with pytest.raises(ValueError):
        v = SubVector(0, 10, 0)
    with pytest.raises(ValueError):
        v = SubVector(0, 10, 400)
    with pytest.raises(ValueError):
        v = SubVector(0, 10, -1)
    with pytest.raises(ValueError):
        v = SubVector(144, -85, 0, 60)

    for n in range(10):
        d = random.randint(0, 100)
        p = random.randint(1, 100) + d
        a = 0
        with pytest.raises(ValueError):
            v = SubVector(d, p, a)
