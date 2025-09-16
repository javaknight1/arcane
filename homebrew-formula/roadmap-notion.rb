class RoadmapNotion < Formula
  desc "AI-powered roadmap generator with automated Notion import"
  homepage "https://github.com/robavery/roadmap-notion"
  url "https://github.com/robavery/roadmap-notion/releases/download/v1.0.0/roadmap-notion-macos"
  sha256 "" # Will be updated automatically by release workflow
  version "1.0.0"

  def install
    bin.install "roadmap-notion-macos" => "roadmap-notion"
  end

  test do
    system "#{bin}/roadmap-notion", "--help"
  end
end