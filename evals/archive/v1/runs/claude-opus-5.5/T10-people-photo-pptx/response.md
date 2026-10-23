The 5-slide Proseware introduction deck is built: `evals/runs/claude-opus-5.5/T10-people-photo-pptx/deck.pptx`. The outline (`outline.yaml`) passed the check with no errors or warnings. Previews are in `render/slide-1.png` to `slide-5.png`.

1. Cover: "Meet your Workday team", "Proseware onboarding", March 2027.
2. Intro: Dana Whitfield, Client Partner, Workday, with the photo in the intro photo frame on the warm intro background.
3. Photo-right: "Our Chicago office" on the left, the photo full height on the right.
4. Two-column: "How Dana will help" with 3 numbered items (Plan, Connect, Review), each with the sentence you gave.
5. Closing: the Workday bumper with "Welcome to Workday" under the logo.

Before you send it:

- **The photo is a placeholder.** `examples/images/sample-photo.png` is the repository's sample image: a simple drawn silhouette on blue, not a real photo. It sits on both slide 2 and slide 3. So Dana's slide doesn't show Dana, and the Chicago office slide doesn't show the office. Put Dana's headshot and an office photo in the repository (for example `decks/images/dana-whitfield.jpg` and `decks/images/chicago-office.jpg`) and I'll swap them in and rebuild. The photo slots crop to fit, so leave some space around Dana's face.
- **Slide 3 has only a title and the photo.** The photo-right layout has no body area, so the left half is white space under "Our Chicago office". If you want a line about the office (address, team size, or what happens there), I can add a content slide after it.

Questions:

1. Can you send Dana's headshot and a photo of the Chicago office?
2. Do you want a short text slide about the Chicago office after slide 3?

The preview PNGs use a substitute font for body text because Archivo Light isn't installed on the render machine. PowerPoint will use Archivo Light if it is installed.
