using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class TargetHitbox : MonoBehaviour, IDamagable
{
    [SerializeField] Target target;
    [SerializeField] float damageMultiplier = 1;


    [Header("Impact VFX")]
    [SerializeField] private GameObject impactVFX;

    private void Start()
    {
        if (target == null)
        {
            target = GetComponentInParent<Target>();
            if (target == null)
                Destroy(this);
        }
    }

    public void ImpactEffect(Vector3 point)
    {
        if (impactVFX == null) return;

        
        // Spawn it at the point of impact, look away from center
        GameObject vfxInstance = VFXPooler.instance.GetVFX(impactVFX);
        if(vfxInstance == null)
        {
            vfxInstance = Instantiate(impactVFX);
        }
        vfxInstance.transform.position = point;
        vfxInstance.transform.LookAt(point + (point - transform.position));
    }

    /// <summary>
    /// Register an effect to the main target, applying any modifier
    /// </summary>
    /// <param name="dmg"></param>
    public void RegisterEffect(float dmg, Vector3 origin)
    {
        target?.RegisterEffect(dmg * damageMultiplier, origin);
    }

    /// <summary>
    /// Register an effect to the main target, applying any damage multiplier. addative with base modifier.
    /// </summary>
    /// <param name="data">Team data to use</param>
    /// <param name="dmgMultiplier">multiplier to add</param>
    public void RegisterEffect(TeamDamage data, Vector3 origin, float dmgMultiplier = 1)
    {
        target?.RegisterEffect(data, origin, dmgMultiplier + damageMultiplier);
    }

    /// <summary>
    /// Get reference to the target of this hitbox
    /// </summary>
    /// <returns></returns>
    public Target Target()
    {
        return target;
    }
}
