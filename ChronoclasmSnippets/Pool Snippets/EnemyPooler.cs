/*
 * ================================================================================================
 * Author - Ben Schuster
 * Date Created - March 27th, 2022
 * Last Edited - March 27th, 2022 by Ben Schuster
 * Description - Manages pooling for all enemies
 * ================================================================================================
 */
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

[System.Serializable]
public class EnemyPool
{
    public EnemySO enemy;
    public int poolSize;
    public int maxSize;
    public int incrementRate;
}

public class EnemyPooler : MonoBehaviour
{
    /// <summary>
    /// Global instance of enemy pooler
    /// </summary>
    public static EnemyPooler instance;

    [Tooltip("All initial enemy pools to use")]
    [SerializeField] private EnemyPool[] enemyPools;

    /// <summary>
    /// Dictionary for enemies : 
    /// Key : Hashcode of enemy name
    /// Value : Pool of instanced enemies
    /// </summary>
    private Dictionary<int, Pool> pool;

    private void Awake()
    {
        if(instance == null)
        {
            instance = this;
            Init();
            onSceneChange.OnEventRaised += ReturnAllToPool;
        }
        else
        {
            Destroy(gameObject);
            return;
        }
    }

    /// <summary>
    /// Initialize the pool based on starting values
    /// </summary>
    protected void Init()
    {
        pool = new Dictionary<int, Pool>();

        // Create a new pool for each option
        foreach (EnemyPool p in enemyPools)
        {
            pool.Add(p.enemy.enemyPrefab.name.GetHashCode(), 
                new Pool(p.enemy.enemyPrefab, p.poolSize, p.maxSize, p.incrementRate, false, transform));
        }
    }

    /// <summary>
    /// Request an enemy from the pool
    /// </summary>
    /// <param name="enemyRequest">Type of enemy to request</param>
    /// <returns>Instanced version of the requested enemy, as a game object</returns>
    public GameObject RequestEnemy(GameObject enemyPrefab)
    {
        int enemyID = enemyPrefab.name.GetHashCode();
        if (pool.ContainsKey(enemyID))
        {
            GameObject enemy = pool[enemyID].Pull();
            if (enemy == null)
            {
                Debug.Log($"ERROR! Enemy from pool was null while requesting {enemyPrefab.name}");
                return null;
            }    
            
            //enemy.transform.parent = null;
            //enemy.GetComponent<EnemyTarget>().PullFromPool(enemyRequest);
            // TODO - any unique enemy functionality here like stat scaling
            return enemy;
        }
        else
        {
            Debug.Log($"[EnemyPooler] Pool of enemy {enemyPrefab.name} does not exist!");
            return null;
        }
    }

    /// <summary>
    /// Return an enemy to the pool
    /// </summary>
    /// <param name="type">Type of enemy to use (its key)</param>
    /// <param name="enemyReturn">Reference to instanced enemy to return</param>
    /// <returns>Whether or not the enemy was returned to the pool</returns>
    public bool Return(GameObject enemyReturn)
    {
        if (enemyReturn == null)
            return false;

        int enemyID = enemyReturn.name.GetHashCode();

        if(pool.ContainsKey(enemyID))
        {
            //Debug.Log($"Enemy {enemyReturn.name} returned to pool");
            // do other funcs when being returned
            //enemyReturn.GetComponent<EnemyTarget>().ReturnToPool();
            pool[enemyID].Return(enemyReturn);
            //enemyReturn.transform.parent = transform;
            return true;
        }
        else
        {
            Debug.Log($"[EnemyPooler] Pool of enemy {enemyReturn.name} is trying to be returned but does not exist!");
            return false;
        }
    
    }

    [SerializeField] private ChannelVoid onSceneChange;

    /// <summary>
    /// Return all objects to the pool instantly. Defined by children
    /// </summary>
    private void ReturnAllToPool()
    {
        for (int i = 0; i < transform.childCount; i++)
        {
            // if an object is out of the pool, return it
            if (transform.GetChild(i) != null && transform.GetChild(i).gameObject.activeInHierarchy)
            {
                Return(transform.GetChild(i).gameObject);
            }
        }
    }
    private void OnDestroy()
    {
        onSceneChange.OnEventRaised -= ReturnAllToPool;
    }
}
