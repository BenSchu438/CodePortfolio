/*
 * ================================================================================================
 * Author - Ben Schuster
 * Date Created - June 5th, 2023
 * Last Edited - June 5th, 2023 by Ben Schuster
 * Description - Interface for poolable objects.
 * ================================================================================================
 */
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public interface IPoolable
{
    /// <summary>
    /// Functionality for when an object is initialized into the pool
    /// </summary>
    void PoolInit();
    /// <summary>
    /// Functionality for when the object is pulled from the pool
    /// </summary>
    void PoolPull();
    /// <summary>
    /// Functionality for when the object is returne to the pool
    /// </summary>
    void PoolPush();
}
