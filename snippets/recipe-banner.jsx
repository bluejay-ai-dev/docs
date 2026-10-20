export const RecipeBanner = ({ focus = "50% 50%" }) => (
  <div className="bj-recipe-banner not-prose" style={{ backgroundPosition: focus }} aria-hidden="true">
    <span className="bj-recipe-banner-mark">
      <span className="bj-card-icon-flywheel" />
      Cookbook
    </span>
  </div>
);
