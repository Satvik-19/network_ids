import { signedContributions } from "../lib/charts";

export function SignedContributions({ features, label }: {
  features: { feature: string; shap_value: number }[]; label: string;
}) {
  const { extent, bars } = signedContributions(features.map(f => f.shap_value));
  return <div className="shap-chart">
    {features.map((f, index) => <div className="shap-row" key={f.feature} title={`${f.feature}: ${f.shap_value}`}>
      <span>{f.feature.replace(/_/g, " ")}</span>
      <div className="shap-track" role="img" aria-label={`${f.feature}: ${f.shap_value}, ${f.shap_value < 0 ? "against" : "toward"} predicted ${label}`}><span className={`shap-bar ${f.shap_value < 0 ? "negative" : ""}`} style={{left:`${bars[index].left}%`,width:`${bars[index].width}%`}} /></div>
      <span className="shap-number">{f.shap_value > 0 ? "+" : ""}{f.shap_value.toFixed(4)}</span>
    </div>)}
    <div className="shap-row"><span /><div className="shap-axis"><span>−{extent.toFixed(3)}</span><span>0</span><span>+{extent.toFixed(3)}</span></div><span /></div>
    <p className="shap-axis-label">SHAP contribution · XGBoost raw margin for {label}</p>
    <p className="meta mt-3">Outlined / left: against prediction. Solid / right: toward prediction. Shared scale across these features; contributions are not probabilities or causal explanations.</p>
  </div>;
}
