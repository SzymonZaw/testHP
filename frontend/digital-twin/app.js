const dialog = document.getElementById('observation-dialog');
const addObservation = document.getElementById('add-observation');
const zoneLabel = document.getElementById('zone-label');

addObservation.addEventListener('click', () => dialog.showModal());

document.querySelectorAll('.zone').forEach((zone) => {
  zone.addEventListener('click', () => {
    document.querySelectorAll('.zone').forEach((item) => item.classList.remove('selected'));
    zone.classList.add('selected');
    zoneLabel.textContent = `Zone ${zone.textContent}`;
  });
});

document.querySelector('.close').addEventListener('click', () => dialog.close());
