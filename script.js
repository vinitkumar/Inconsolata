const faceSelect = document.querySelector("#face-select");
const sizeRange = document.querySelector("#size-range");
const ligatureToggle = document.querySelector("#ligature-toggle");
const tester = document.querySelector("#tester");

function updateTester() {
  const isNarrow = faceSelect.value === "narrow";
  tester.style.fontFamily = isNarrow
    ? '"Demo Inconsolata Narrow", "Demo Inconsolata", ui-monospace, monospace'
    : '"Demo Inconsolata", ui-monospace, monospace';
  tester.style.fontSize = `${sizeRange.value}px`;
  tester.style.fontFeatureSettings = ligatureToggle.checked
    ? '"liga" 1, "dlig" 1, "calt" 1'
    : '"liga" 0, "dlig" 0, "calt" 0';
}

faceSelect.addEventListener("change", updateTester);
sizeRange.addEventListener("input", updateTester);
ligatureToggle.addEventListener("change", updateTester);
updateTester();
