require_relative "contacts"


describe "parse_agency" do
  it "doesn't overwrite agency name" do
    html = StringIO.new("<h1>An Agency</h1>" \
                        "<h2>I want to make a FOIA request to:" \
                        "   <select>" \
                        "     <option value='0'>Select an Office</option>" \
                        "     <option value='1'>First Office</option>" \
                        "     <option value='2'>Second Office</option>" \
                        "   </select>" \
                        "</h2>" \
                        "<div id='0'>Default</div>" \
                        "<div id='1'>Description of office 1</div>" \
                        "<div id='2'>Description of office 2</div>" \
                        "<h2>About</h2>Some description")
    allow(File).to receive(:read).and_return(html)
    allow(self).to receive(:parse_department).and_return("Desc 1", "Desc 2")
    result = parse_agency("age", "some/path")
    expect(result["abbreviation"]).to eq("age")
    expect(result["name"]).to eq("An Agency")
    expect(result["description"]).to eq("Some description")
  end

  it "allows BRs in description" do
    html = StringIO.new("<h1>An Agency</h1>" \
                        "<h2>I want to make a FOIA request to:" \
                        "<option value='0'>Select an Office</option>" \
                        "</h2>" \
                        "<div id='0'>Default</div>" \
                        "<h2>About</h2>Line 1<br>Line 2<br><br>Last Line")
    allow(File).to receive(:read).and_return(html)
    result = parse_agency("age", "some/path")
    expect(result["description"]).to eq("Line 1\nLine 2\nLast Line")
  end
end
