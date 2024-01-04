from __future__ import annotations

import math


class Vector3(object):
    """
    A class representing a 3-dimensional vector.
    """

    __slots__ = ("_data")

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> None:
        """
        Initialize a Vector3 object.

        Args:
            x (float): The x-coordinate of the vector. Default is 0.0.
            y (float): The y-coordinate of the vector. Default is 0.0.
            z (float): The z-coordinate of the vector. Default is 0.0.
        """
        self._data = [x, y, z]

    def __repr__(self) -> str:
        """
        Return a string representation of this Vector3.

        Returns:
            str: A string representation of the Vector3 object.
        """
        return f"Vector3 ({self.x()}, {self.y()}, {self.z()})"

    def x(self) -> float:
        """
        Get the x-coordinate of the vector.

        Returns:
            float: The x-coordinate of the vector.
        """
        return self._data[0]

    def setX(self, newValue: float) -> None:
        """
        Set the x-coordinate of the vector.

        Args:
            newValue (float): The new value for the x-coordinate.
        """
        self._data[0] = float(newValue)

    def y(self) -> float:
        """
        Get the y-coordinate of the vector.

        Returns:
            float: The y-coordinate of the vector.
        """
        return self._data[1]

    def setY(self, newValue: float) -> None:
        """
        Set the y-coordinate of the vector.

        Args:
            newValue (float): The new value for the y-coordinate.
        """
        self._data[1] = float(newValue)

    def z(self) -> float:
        """
        Get the z-coordinate of the vector.

        Returns:
            float: The z-coordinate of the vector.
        """
        return self._data[2]

    def setZ(self, newValue: float) -> None:
        """
        Set the z-coordinate of the vector.

        Args:
            newValue (float): The new value for the z-coordinate.
        """
        self._data[2] = float(newValue)

    def scalarProduct(self, value: float) -> 'Vector3':
        """
        Compute the scalar product of the vector with a scalar value.

        Args:
            value (float): The scalar value.

        Returns:
            Vector3: The resulting vector after scalar multiplication.
        """
        return Vector3(self.x() * value, self.y() * value, self.z() * value)

    def dotProduct(self, vec3: 'Vector3') -> float:
        """
        Compute the dot product of the vector with another vector.

        Args:
            vec3 (Vector3): The other vector.

        Returns:
            float: The dot product of the two vectors.
        """
        return (self.x() * vec3.x()) + (self.y() * vec3.y()) + (self.z() * vec3.z())

    def crossProduct(self, vec3: 'Vector3') -> 'Vector3':
        """
        Compute the cross product of the vector with another vector.

        Args:
            vec3 (Vector3): The other vector.

        Returns:
            Vector3: The cross product of the two vectors.
        """
        return Vector3(
            self.y() * vec3.z() - self.z() - vec3.y(),
            self.z() * vec3.x() - self.x() * vec3.z(),
            self.x() * vec3.y() - self.y() * vec3.x()
        )

    def length(self) -> float:
        """
        Compute the length of the vector.

        Returns:
            float: The length of the vector.
        """
        x: float = self.x() * self.x()
        y: float = self.y() * self.y()
        z: float = self.z() * self.z()
        return math.sqrt(x + y + z)

    def normalized(self) -> 'Vector3':
        """
        Compute the normalized vector.

        Returns:
            Vector3: The normalized vector.
        """
        length: float = self.length()
        if length == 0:
            return Vector3(0, 0, 0)
        return Vector3(self.x() / length, self.y() / length, self.z() / length)

    def distance(self, vec3: 'Vector3') -> float:
        """
        Compute the distance between this vector and another vector.

        Args:
            vec3 (Vector3): The other vector.

        Returns:
            float: The distance between the two vectors.
        """
        xDistance: float = vec3.x() - self.x()
        yDistance: float = vec3.y() - self.y()
        zDistance: float = vec3.z() - self.z()
        return math.sqrt(xDistance * xDistance + yDistance * yDistance + zDistance * zDistance)

    def __neg__(self) -> 'Vector3':
        """
        Compute the negation of the vector.

        Returns:
            Vector3: The negated vector.
        """
        return Vector3(-self.x(), -self.y(), -self.z())

    def __mul__(self, val: 'Vector3' | float) -> float | 'Vector3':
        """
        Multiply the vector by a scalar value or compute the dot product with another vector.

        Args:
            val (Vector3 | float): The scalar value or the other vector.

        Returns:
            float | Vector3: The result of the multiplication or dot product.
        """
        if isinstance(val, Vector3):
            # Vector 3 is given, return a Dot Product
            return self.dotProduct(val)
        # Single value is given, return a Scalar Product
        return self.scalarProduct(val)

    def __div__(self, value: float) -> 'Vector3':
        """
        Divide the vector by a scalar value.

        Args:
            value (float): The scalar value.

        Returns:
            Vector3: The resulting vector after division.
        """
        return Vector3(self.x() / value, self.y() / value, self.z() / value)

    def __add__(self, vec3: 'Vector3') -> 'Vector3':
        """
        Add the vector with another vector.

        Args:
            vec3 (Vector3): The other vector.

        Returns:
            Vector3: The resulting vector after addition.
        """
        return Vector3(self.x() + vec3.x(), self.y() + vec3.y(), self.z() + vec3.z())

    def __sub__(self, vec3: 'Vector3') -> 'Vector3':
        """
        Subtract another vector from the vector.

        Args:
            vec3 (Vector3): The other vector.

        Returns:
            Vector3: The resulting vector after subtraction.
        """
        return Vector3(self.x() - vec3.x(), self.y() - vec3.y(), self.z() - vec3.z())

    def __eq__(self, vec3: 'Vector3') -> bool:
        """
        Check if the vector is equal to another vector.

        Args:
            vec3 (Vector3): The other vector.

        Returns:
            bool: True if the vectors are equal, False otherwise.
        """
        return self.x == vec3.x and self.y == vec3.y and self.z == vec3.z

    def __ne__(self, vec3: 'Vector3') -> bool:
        """
        Check if the vector is not equal to another vector.

        Args:
            vec3 (Vector3): The other vector.

        Returns:
            bool: True if the vectors are not equal, False otherwise.
        """
        return not self == vec3

    def __xor__(self, vec3: 'Vector3') -> 'Vector3':
        """
        Compute the cross product of the vector with another vector.

        Args:
            vec3 (Vector3): The other vector.

        Returns:
            Vector3: The cross product of the two vectors.
        """
        return Vector3(
            self.y() * vec3.z() - self.z() * vec3.y(),
            self.z() * vec3.x() - self.x() * vec3.z(),
            self.x() * vec3.y() - self.y() * vec3.x()
        )

    def copy(self) -> 'Vector3':
        """
        Create a copy of the vector.

        Returns:
            Vector3: A copy of the vector.
        """
        return Vector3(self.x(), self.y(), self.z())

