
// HEADER REDACTED //

/// <summary>
/// Manages the disaster information to quickly and automatically load
/// </summary>
public class DisasterInfoLoader : MonoBehaviour
{
	[Tooltip("The image object that will hold the ability's icon")]
	[SerializeField] private Image icon;
	[Tooltip("The text object that will hold the ability's text description")]
	[SerializeField] private TextMeshProUGUI desc;
	[Tooltip("The video object that will manage the ability's video")]
	[SerializeField] private VideoPlayer videoPlayer;
	[Tooltip("The expanded view object that is called when selected")]
	[SerializeField] private ExpandedViewManager expandedView;

	[Tooltip("Disaster data to load into this segment")]
	[SerializeField] private AbilityData loadedDisaster;

	/// <summary>
	/// Load in the data for this info panel
	/// </summary>
	private void Start()
	{
		if (loadedDisaster == null)
		{
			Debug.LogError("Instruction menu trying to load null info!");
			Destroy(this.gameObject);
			return;
		}

		icon.sprite = loadedDisaster.MenuIcon;
		desc.text = loadedDisaster.AbilityDescription;
		videoPlayer.clip = loadedDisaster.AbilityVideo;
		videoPlayer.targetTexture = loadedDisaster.VideoTargetTexture;
		videoPlayer.gameObject.GetComponent<RawImage>().texture = loadedDisaster.VideoTargetTexture;
	}

	/// <summary>
	/// Send this ability's data to the expanded view so it can load
	/// </summary>
	public void LoadExpandedView()
	{
		expandedView.LoadNewAbility(loadedDisaster);
		expandedView.gameObject.SetActive(true);
	}
}