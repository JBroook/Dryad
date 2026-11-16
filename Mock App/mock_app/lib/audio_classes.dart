const List<String> audioClassNames = [
  'Fire',
  'Rain',
  'Thunderstorm',
  'WaterDrops',
  'Wind',
  'Silence',
  'TreeFalling',
  'Helicopter',
  'VehicleEngine',
  'Axe',
  'Chainsaw',
  'Generator',
  'Handsaw',
  'Firework',
  'Gunshot',
  'WoodChop',
  'Whistling',
  'Speaking',
  'Footsteps',
  'Clapping',
  'Insect',
  'Frog',
  'BirdChirping',
  'WingFlaping',
  'Lion',
  'WolfHowl',
  'Squirrel',
];

const Map<String, String> audioThreatClassNames = {
  'Chainsaw': 'Chainsaw',
  'Generator': 'Generator',
  'Handsaw': 'Handsaw',
  'Fire': 'Fire',
  'TreeFalling': 'Treefall',
  'VehicleEngine': 'Vehicles',
  'Gunshot': 'Gun Shot',
  'WoodChop': 'Wood Chopping',
};

class ThreatDetection {
  const ThreatDetection({
    required this.threatClassId,
    required this.threatClassName,
    required this.confidence,
  });

  final int threatClassId;
  final String threatClassName;
  final int confidence;
}

ThreatDetection? selectThreatDetection({
  required List<double> scores,
  required List<int> configuredThreatClassIds,
  required Map<int, String> threatClassNames,
  required int confidenceThreshold,
}) {
  if (scores.length != audioClassNames.length) {
    return null;
  }

  ThreatDetection? selected;
  var selectedScore = confidenceThreshold / 100;
  for (var index = 0; index < scores.length; index++) {
    final score = scores[index];
    final threatClassName = audioThreatClassNames[audioClassNames[index]];
    if (threatClassName == null ||
        !score.isFinite ||
        score < 0 ||
        score > 1 ||
        score * 100 <= confidenceThreshold) {
      continue;
    }

    for (final threatClassId in configuredThreatClassIds) {
      if (threatClassNames[threatClassId] == threatClassName &&
          score > selectedScore) {
        selected = ThreatDetection(
          threatClassId: threatClassId,
          threatClassName: threatClassName,
          confidence: (score * 100).round(),
        );
        selectedScore = score;
      }
    }
  }

  return selected;
}
