/*
 * ================================================================================================
 * Author - Ben Schuster
 * Date Created - March 27th, 2023
 * Last Edited - March 27th, 2023 by Ben Schuster
 * Description - Individual pool object. Does not contain any unique functionality as that 
 * will be handled by concrete pool managers
 * ================================================================================================
 */
using System.Collections;
using System.Collections.Generic;
using System.Drawing;
using UnityEngine;

[System.Serializable]
public class Pool
{
    /// <summary>
    /// Primary key for this pool
    /// </summary>
    private GameObject key;
    /// <summary>
    /// Hashcode of the key object
    /// </summary>
    private int keyID;
    /// <summary>
    /// Queue of current objects in pool
    /// </summary>
    private Queue<GameObject> currentPool;
    /// <summary>
    /// Current size of the queue
    /// </summary>
    private int size;
    /// <summary>
    /// Maximum size of this pool
    /// </summary>
    private int maxSize;
    /// <summary>
    /// Increment rate to increase size by when pool is empty
    /// </summary>
    private int incrementRate;
    /// <summary>
    /// Whether this pool recycles the oldest object at max
    /// </summary>
    private bool recycle;
    /// <summary>
    /// Root gameobject to store pooled objects under
    /// </summary>
    private Transform container;
    
    /// <summary>
    /// Constructor for pool
    /// </summary>
    /// <param name="key">Key for this pool</param>
    /// <param name="size">starting size for this pool</param>
    /// <param name="maxSize">max size of this pool</param>
    /// <param name="incrementRate">increment rate for this pool</param>
    /// <param name="container">root to store pooled objects under</param>
    public Pool(GameObject key, int size, int maxSize, int incrementRate, bool recycle, Transform container)
    {
        // prepare variables
        this.key = key;
        this.keyID = key.name.GetHashCode();
        this.size = size;
        this.maxSize = maxSize;
        this.incrementRate = incrementRate;
        this.recycle = recycle;
        this.container = container;

        // create pool queue, populate to requested size
        currentPool = new Queue<GameObject>();

        // Init pool with starting values
        Init();
    }

    /// <summary>
    /// Initialize the pool with new values
    /// </summary>
    protected void Init()
    {
        // if no queue, create it
        if(currentPool == null)
        {
            currentPool = new Queue<GameObject>();
        }

        // populate buffer with current size size
        for (int i = 0; i < size; i++)
        {
            Spawn();
        }
    }

    /// <summary>
    /// Extend the pool by its increment rate. Return a new object from the extended pool
    /// </summary>
    /// <returns>A newely pooled object. If null, then pool is maxed.</returns>
    protected GameObject ExtendPool()
    {
        // make sure the pool exists first
        if(currentPool == null)
        {
            currentPool = new Queue<GameObject>();
        }
        // check if going out of bounds
        if(size >= maxSize)
        {
            Debug.Log($"[POOL] Pool of {key} is maxed out!");
            return null;
        }

        // increase size, clamp it
        int newSize = Mathf.Clamp(size + incrementRate, 0, maxSize);

        // fill queue with the new amount of objects. Keep same name for hashcode reasons
        for (int i = 0; i < (newSize - size); i++)
        {
            Spawn();
        }

        // update size, return one of the new objects
        // do this because this will only ever be called when attempting to pull an object
        size = newSize;
        return currentPool.Dequeue();
    }

    /// <summary>
    /// Actually spawn the object into the pool
    /// </summary>
    private void Spawn()
    {
        GameObject spawnBuffer;
        spawnBuffer = MonoBehaviour.Instantiate(key, container);
        spawnBuffer.SetActive(false);
        IPoolable poolRef = spawnBuffer.GetComponent<IPoolable>();
        
        if(poolRef != null)
        {
            poolRef.PoolInit();
            spawnBuffer.name = key.name;
            currentPool.Enqueue(spawnBuffer);
        }
        else
        {
            Debug.Log($"Error trying to initialize {key.name} in pool, excluding from pool");
            return;
        }
    }

    /// <summary>
    /// Pull an object from the pool 
    /// </summary>
    /// <returns>A pooled object. If null, the pool is maxed.</returns>
    public GameObject Pull()
    {
        GameObject o;
        // Get an object from the pool
        if (currentPool.Count > 0)
        {
            o = currentPool.Dequeue();
        }
        // Otherwise extend the pool
        else
        {
            o = ExtendPool();
        }

        // If set to recycle, make sure to reset it just incase.
        // Add to end of pool queue
        if (recycle && o != null)
        {
            o.SetActive(false);
            o.GetComponent<IPoolable>().PoolPush();
            currentPool.Enqueue(o);
        }

        if(o != null)
        {
            o.GetComponent<IPoolable>()?.PoolPull();
            o.SetActive(true);
        }

        return o;
    }

    /// <summary>
    /// Return an object reference to this current pool
    /// </summary>
    /// <param name="objectRef">Reference to the key object</param>
    public void Return(GameObject objectRef)
    {
        // make sure pool is used 
        if (currentPool == null)
        {
            currentPool= new Queue<GameObject>();
        }

        // add object back to queue
        objectRef.transform.localPosition= Vector3.zero;
        objectRef.GetComponent<IPoolable>().PoolPush();
        objectRef.SetActive(false);
        
        // Recycled pools should already have this in it
        // so double check 
        if(!currentPool.Contains(objectRef))
            currentPool.Enqueue(objectRef);
    }

    /// <summary>
    /// The key for this pool
    /// </summary>
    /// <returns>Key for this pool as a hashcode of the name</returns>
    public int Key()
    {
        return keyID;
    }
}
