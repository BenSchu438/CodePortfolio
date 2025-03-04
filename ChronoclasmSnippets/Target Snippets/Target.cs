/*
 * ================================================================================================
 * Author - Ben Schuster
 * Date Created - February 2nd, 2022
 * Last Edited - February 2nd, 2022 by Ben Schuster
 * Description - Base class for ALL targetable entities
 * ================================================================================================
 */
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Sirenix.OdinInspector;

public enum Team
{
    UNASSIGNED,
    PLAYER,
    ENEMY,
    WORLD
}


[System.Serializable]
public class DroppableQuantity
{
    [AssetsOnly] public GameObject spawnObject;
    public Vector2 quantityRange;
    [Range(0, 100)] public float dropChance;
}

[RequireComponent(typeof(HealthManager))]
public abstract class Target : TimeAffectedEntity, IDamagable, TimeObserver
{
    [Header("Core Target Info")]

    [Tooltip("The center point of this entity, used for targeting and spawning")]
    [SerializeField] protected Transform _center;
    [Tooltip("The team this target is a part of")]
    [SerializeField] protected Team _team = Team.UNASSIGNED;
    [Tooltip("The threat of this target, used for AI targeting")]
    [SerializeField] protected float _targetThreat = 0;
    [Tooltip("Whether or not this target is killable. Unkillable targets still take damage but cannot die.")]
    [SerializeField] protected bool _unkillable;
    /// <summary>
    /// Rigidbody for this target, if it exists
    /// </summary>
    protected Rigidbody _rb;

    /// <summary>
    /// The manager controlling health for this target
    /// </summary>
    protected HealthManager _healthManager;

    /// <summary>
    /// Whether or not this entity has already been killed
    /// </summary>
    protected bool _killed = false;

    [Header("Core Gameplay Features")]

    [Tooltip("Whether or not this target is immune to knockback")]
    [SerializeField] protected bool immuneToKnockback = true;
    [ShowIf("@this.immuneToKnockback == false")]
    [SerializeField] protected float knockbackModifier = 1f;
    [ShowIf("@this.immuneToKnockback == false")]
    [SerializeField] protected float maxKnockback;

    /// <summary>
    /// Any knockback stored during timestop
    /// </summary>
    protected Vector3 storedKnockback;

    [Tooltip("If enabled, this target can not take damage until the shield is destroyed")]
    [SerializeField] protected ShieldTarget invincibilityShield;

    // The manger controlling buffs and debuffs for this target
    //private EffectManager _effectManager;

    [Header("Core Visual Info")]

    [SerializeField, AssetsOnly] protected GameObject _deathVFX;
    [SerializeField] protected float _deathVFXScaleMod;

    [Tooltip("Damage made when this target is damaged")]
    [SerializeField] protected AudioClipSO damagedSound;
    [Tooltip("Damage made when this target is killed")]
    [SerializeField] protected AudioClipSO deathSound;

    [Tooltip("Cooldown between ability for damaged sound effect play")]
    [SerializeField] private float damagedSoundCooldown = 0.5f;

    protected ScaledTimer damagedSoundCooldownTracker;

    [Header("Drop Stuff")]
    [SerializeField] protected List<DroppableQuantity> dropList;

    /// <summary>
    /// the origin direction of the last attack
    /// </summary>
    protected Vector3 lastDamageOrigin;
    /// <summary>
    /// The damage taken last frame, scaled via timestop
    /// </summary>
    protected float damageLastFrame;

    /// <summary>
    /// Audiosource for this target
    /// </summary>
    protected AudioSource audioSource;

    protected virtual void Awake()
    {
        _healthManager = GetComponent<HealthManager>();
        _rb = GetComponent<Rigidbody>();
        audioSource = GetComponent<AudioSource>();

        damagedSoundCooldownTracker = new ScaledTimer(damagedSoundCooldown, false);
        damagedSoundCooldownTracker.ResetTimer();
        // If initialization of health manager fails, destroy itself
        if (_healthManager == null || !_healthManager.Init())
        {
            KillTarget();
        }
    }

    protected virtual void Update()
    {
        // scale health manager and shield manager if it exists
        _healthManager.timeScale = Timescale;

        // if time isnt stopped, reset damage since last frame
        if (!Slowed && !_killed)
        {
            damageLastFrame = 0;
        }
    }

    /// <summary>
    /// Register an effect against this target.
    /// </summary>
    /// <param name="dmg">PLACEHOLDER - pass damage to deal to this target</param>
    public virtual void RegisterEffect(float dmg, Vector3 origin)
    {
        if(!AffectedByAttacks()) return;

        damageLastFrame += dmg;
        lastDamageOrigin = origin;

        if (!_killed)
        {
            if (damagedSoundCooldownTracker != null && damagedSoundCooldownTracker.TimerDone())
            {
                damagedSound.PlayClip(_center, audioSource);
                damagedSoundCooldownTracker.ResetTimer();
            }

            // if the target is out of health...
            if (_healthManager.Damage(dmg))
            {
                if (_unkillable)
                    return;

                _killed = true;
                KillTarget();
            }
        }
            
    }

    public virtual void RegisterEffect(TeamDamage data, Vector3 origin, float dmgMultiplier = 1)
    {
        if(!AffectedByAttacks() || data == null) return;

        // Check which damage profile needs to be used, if available
        TeamDmgProfile profile = data.GetTeam(_team);
        if (profile == null || profile.team != _team || !profile.active) return;

        // pass in the damage
        RegisterEffect(profile.damage*dmgMultiplier, origin);
    }

    /// <summary>
    /// Whether or not this target can be affected by attacks
    /// </summary>
    /// <returns></returns>
    protected virtual bool AffectedByAttacks()
    {
        // if a shield is enabled, dont take damage
        if (invincibilityShield != null && invincibilityShield.isActiveAndEnabled)
            return false;


        return !_killed && gameObject.activeInHierarchy;
    }

    /// <summary>
    /// Kill this target. Default with little functionality
    /// </summary>
    protected virtual void KillTarget()
    {
        DeathEffects();

        DropAllObjs();

        // Debug.Log($"Entity {gameObject.name} has been killed but does not have its own kill function, destroying self.");
        DestroyObject();
    }

    protected virtual void DestroyObject()
    {
        Destroy(gameObject);
    }

    public void DropAllObjs()
    {
        foreach (DroppableQuantity obj in dropList)
        {
            SpawnDrops(obj.spawnObject, obj.dropChance, obj.quantityRange);
        }
    }

    public void DeathEffects()
    {
        deathSound.PlayClip(_center);

        if (_deathVFX != null)
        {
            GameObject o = Instantiate(_deathVFX, _center.position, Quaternion.identity);
            o.transform.localScale *= _deathVFXScaleMod;
        }
    }

    /// <summary>
    /// Inturrupt the target. By default, do nothing.
    /// </summary>
    public virtual void Inturrupt()
    {
        return;
    }

    /// <summary>
    /// Reset the core values of the target
    /// </summary>
    public virtual void ResetTarget()
    {
        _killed = false;
        _healthManager?.ResetHealth();

        if (invincibilityShield != null)
        {
            invincibilityShield.ResetTarget();
        }
            
    }

    /// <summary>
    /// Determine if drops should drop, and spawn them
    /// </summary>
    protected void SpawnDrops(GameObject orb, float dropChance, Vector2 dropAmountRange)
    {
        // Roll the dice. If the value is higher than the value, exit
        if (Random.Range(1f, 100f) > dropChance || orb is null)
        {
            return;
        }

        int spawnAmount = Random.Range((int)dropAmountRange.x, (int)dropAmountRange.y);

        // Spawn the randomized amount at random ranges, as long as they aren't intersecting
        for (int i = 0; i < spawnAmount; i++)
        {
            // Spawn objects, apply rotation and velocity
            if (_center != null)
            {
                if(ProjectilePooler.instance != null && ProjectilePooler.instance.HasPool(orb))
                {
                    GameObject t = ProjectilePooler.instance.GetProjectile(orb);
                    if(t != null)
                    {
                        t.transform.position = _center.position;
                    }   
                }
                else
                {
                    Instantiate(orb, _center.position, Quaternion.identity);
                }
            }
                
        }
    }

    public virtual void Knockback(float force, float verticalForce, Vector3 origin)
    {
        if (!AffectedByAttacks())
        {
            return;
        }
           
        // make sure knockback can be applied
        if (immuneToKnockback || _rb == null || _rb.isKinematic || (force + verticalForce <= 0))
        {
            return;
        }

        // Calculate force vector, draw for debug reasons
        Vector3 forceVector = (_center.position - origin);
        forceVector.y = 0;
        forceVector = forceVector.normalized;
        forceVector *= force;
        forceVector += Vector3.up * verticalForce;
        forceVector *= knockbackModifier;
        // Clamp max knockback
        if (forceVector.magnitude > maxKnockback)
            forceVector = forceVector.normalized * maxKnockback;
        //Debug.DrawRay(origin, forceVector, Color.red, 3f);

        // If currently frozen, store knockback but dont apply it
        if (Affected && Slowed)
        {
            storedKnockback += forceVector;
        }
        // Otherwise, directly apply it
        else
        {
            // Zero current velocity, apply new force
            _rb.velocity = Vector3.zero;
            _rb.AddForceAtPosition(forceVector, _center.position, ForceMode.Impulse);
        }
    }

    public virtual void Knockback(TeamDamage data, Vector3 origin, float multiplier = 1)
    {
        TeamDmgProfile profile = data.GetTeam(_team);

        // apply knockback if there is any
        if(profile != null && (profile.horizontalKnockback + profile.verticalKnockback > 0))
        {
            Knockback(profile.horizontalKnockback * multiplier, profile.verticalKnockback * multiplier, origin);
        }
    }

    #region Getters

    /// <summary>
    /// The center point of this entity, used for targeting and spawning
    /// </summary>
    public Transform Center
    {
        get { return _center; }
    }
    /// <summary>
    /// The team this target is a part of
    /// </summary>
    public Team Team
    {
        get { return _team; }
    }
    /// <summary>
    /// The threat of this target, used for AI targeting
    /// </summary>
    public float Threat
    {
        get { return _targetThreat; }
    }

    /// <summary>
    /// Whether or not this target is killed
    /// </summary>
    /// <returns></returns>
    public bool Killed()
    {
        return _killed;
    }

    public bool Killable()
    {
        return !_unkillable;
    }

    Target IDamagable.Target()
    {
        return this;
    }



    #endregion

    public virtual void OnStop()
    {
        storedKnockback = Vector3.zero;
    }

    public virtual void OnResume()
    {
        if(storedKnockback.magnitude > 0)
        {
            _rb.velocity = Vector3.zero;
            _rb.AddForce(storedKnockback, ForceMode.Impulse);
        }
    }

    protected virtual void OnEnable()
    {
        //TimeManager.instance.Subscribe(this);
    }

    protected virtual void OnDisable()
    {
        //TimeManager.instance.UnSubscribe(this);
    }
}
