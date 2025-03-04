
// HEADER REDACTED //

/// <summary>
/// Manages behavior of the hippo suck hazard
/// </summary>s
public class HippoController : MonoBehaviour, IHazard
{
	[Tooltip("Duration of the hippo suck")]
	[SerializeField] private float windTime;

	[Tooltip("Strength of the hippo suck")]
	[SerializeField] private float windForce;

	[Tooltip("Offset delay for this hippo")]
	[SerializeField] private float delayTime;

	[Tooltip("Location of sound event")]
	[FMODUnity.EventRef]
	[SerializeField] private string hippoSound;
	[SerializeField] private GameObject soundSphere;

	[Tooltip("Force used when opening mouth")]
	[SerializeField] private float openForce = 350;
	[Tooltip("Force used when closing mouth")]
	[SerializeField] private float closeForce = 3500;

	[Tooltip("Reference to hippo wind")]
	[SerializeField] private GameObject windRef;
	[Tooltip("Reference to deathbox")]
	[SerializeField] private GameObject deathbox;
	[Tooltip("Reference to mouth funnel")]
	[SerializeField] private GameObject mouthFunnel;

	[Tooltip("What starting time to use when playing the hippo immediatly")]
	[SerializeField] private float immediateStarting;

	[Tooltip("What offset multiplier to use when playing the hippo immediatly")]
	[SerializeField] private float immediateOffsetMultiplier;
		

	/// <summary>
	/// Hinge joint for the hippo mouth
	/// </summary>
	private HingeJoint hippoMouth;

	/// <summary>
	/// Get initial references for the object, begin hazard
	/// </summary>
	private void Start()
	{
		// Set hippomouth
		hippoMouth = GetComponentInChildren<HingeJoint>();

		// Set force for wind objects
		HippoWind[] windRef = GetComponentsInChildren<HippoWind>(true);
		foreach(HippoWind wind in windRef)
		{
			wind.SetForce(windForce);
		}

		// Edit the opening/closing power based on scale [otherwise, hippo break] 
		openForce *= transform.parent.gameObject.transform.localScale.x;
		closeForce *= transform.parent.gameObject.transform.localScale.x;

		// Manage initial offset
		// If delay time is negative, then this hippo is waiting for a manual start from a
		// different script
		if (delayTime >= 0)
		{
			RunHazard();
		}			
	}

	/// <summary>
	/// Immediatly starts the hippo animation
	/// </summary>
	public void RunHazardImmediate()
	{
		Animator anim = gameObject.GetComponent<Animator>();
		anim.Play("HippoLoop", 0, (immediateStarting + immediateOffsetMultiplier));
	}

	/// <summary>
	/// Freezes the hippo
	/// </summary>
	public void StopHazard()
	{
		GetComponent<Animator>().StopPlayback();
	}

	/// <summary>
	/// Starts the hippo after a predetermined offset time
	/// </summary>
	public void RunHazard()
	{
		StartCoroutine(OffsetLoop());
	}
		
	/// <summary>
	/// Stop animation for a few seconds to allow for an offset
	/// </summary>
	/// <returns></returns>
	private IEnumerator OffsetLoop()
	{
		yield return new WaitForSeconds(delayTime);
		GetComponent<Animator>().SetBool("startHippo", true);
	}

	/// <summary>
	/// Behavior of opening the hippo mouth
	/// </summary>
	private void OpenMouth()
	{
		// A bit redundent right now, but can be used when audio/VFX needs to be added
		ChangeMouth(openForce, 90f);
	}

	/// <summary>
	/// Start the sound for the hippo
	/// </summary>
	public void PlaySound()
	{
		RuntimeManager.PlayOneShotAttached(hippoSound, soundSphere);
	}

	/// <summary>
	/// Start the hippo sucking
	/// </summary>
	private void StartSuck()
	{
		mouthFunnel.SetActive(true);
		windRef.SetActive(true);
	}

	/// <summary>
	/// End the hippo sucking
	/// </summary>
	private void EndSuck()
	{
		windRef.SetActive(false);
	}
		
	/// <summary>
	/// Activate the death trigger
	/// </summary>
	private void StartDeathTrigger()
	{
		deathbox.SetActive(true);
	}

	/// <summary>
	/// Deactivate the death trigger
	/// </summary>
	private void EndDeathTrigger()
	{
		deathbox.SetActive(false);
	}

	/// <summary>
	/// Behavior of closing the hippo mouth
	/// </summary>
	private void CloseMouth()
	{
		// A bit redundent right now, but can be used when audio/VFX needs to be added
		ChangeMouth(closeForce, -90f);
		mouthFunnel.SetActive(false);
	}

	/// <summary>
	/// Adjust the mechanism that opens/closes the hippo mouth
	/// </summary>
	/// <param name="newForce"></param> Set the force the hippo's mouth moves at
	/// <param name="newTarPos"></param>  Set the new target position [direction it opens/closes]
	/// This value does not define its maximum/minimum rotation range
	private void ChangeMouth(float newForce, float newTarPos)
	{
		// Create new spring, set new values, and set new spring
		JointSpring newSpring = hippoMouth.spring;
		newSpring.spring = newForce;
		newSpring.targetPosition = newTarPos;
		hippoMouth.spring = newSpring;
	}
}