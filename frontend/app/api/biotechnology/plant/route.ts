import { NextRequest, NextResponse } from "next/server";
import { GoogleGenAI } from "@google/genai";

export const runtime = "nodejs";
export const maxDuration = 60;

const MODEL = "gemini-3.5-flash-lite";

type PlantCandidate = {
  scientificName: string;
  commonName: string;
  confidence: string;
  reasoning: string;
};

async function fetchJson(url: string) {
  const response = await fetch(url, {
    headers: { Accept: "application/json" },
    cache: "no-store",
    signal: AbortSignal.timeout(12000),
  });

  if (!response.ok) {
    throw new Error(`External source returned HTTP ${response.status}`);
  }

  return response.json();
}

async function identifyFromImage(
  apiKey: string,
  imageBase64: string,
  mimeType: string
): Promise<PlantCandidate[]> {
  const ai = new GoogleGenAI({ apiKey });

  const response = await ai.models.generateContent({
    model: MODEL,
    contents: [
      {
        role: "user",
        parts: [
          {
            text: `Examine this plant photograph for botanical research.
Return ONLY valid JSON in this schema:
{"candidates":[{"scientificName":"...","commonName":"...","confidence":"low|medium|high","reasoning":"visible identifying features"}]}
Return up to three plausible candidates. If identification is not possible, return {"candidates":[]}.
Do not claim definitive identification from an image. Do not infer edibility,
toxicity, medicinal effectiveness, or safety. Never invent a scientific name.`,
          },
          {
            inlineData: {
              mimeType,
              data: imageBase64,
            },
          },
        ],
      },
    ],
    config: {
      temperature: 0.1,
      maxOutputTokens: 700,
    },
  });

  const text = response.text?.trim() || "";
  const jsonText = text
    .replace(/^```(?:json)?\s*/i, "")
    .replace(/\s*```$/, "");

  const parsed = JSON.parse(jsonText);
  if (!Array.isArray(parsed.candidates)) return [];

  return parsed.candidates
    .filter(
      (item: any) =>
        item &&
        typeof item.scientificName === "string" &&
        item.scientificName.trim()
    )
    .slice(0, 3)
    .map((item: any) => ({
      scientificName: item.scientificName.trim(),
      commonName:
        typeof item.commonName === "string" ? item.commonName.trim() : "",
      confidence: ["low", "medium", "high"].includes(item.confidence)
        ? item.confidence
        : "low",
      reasoning:
        typeof item.reasoning === "string" ? item.reasoning.trim() : "",
    }));
}

async function getTaxonomy(scientificName: string) {
  const url = new URL("https://api.gbif.org/v1/species/match");
  url.searchParams.set("name", scientificName);
  url.searchParams.set("verbose", "true");

  try {
    const data = await fetchJson(url.toString());

    if (!data.scientificName || !data.rank || data.matchType === "NONE") {
      return { available: false, source: "GBIF", record: null };
    }

    return {
      available: true,
      source: "GBIF",
      sourceUrl: `https://www.gbif.org/species/${data.usageKey ?? data.taxonID ?? ""}`,
      record: {
        scientificName: data.scientificName ?? null,
        canonicalName: data.canonicalName ?? null,
        rank: data.rank ?? null,
        kingdom: data.kingdom ?? null,
        phylum: data.phylum ?? null,
        class: data.class ?? null,
        order: data.order ?? null,
        family: data.family ?? null,
        genus: data.genus ?? null,
        species: data.species ?? null,
        taxonomicStatus: data.status ?? null,
        matchType: data.matchType ?? null,
        confidence: data.confidence ?? null,
        usageKey: data.usageKey ?? null,
      },
    };
  } catch {
    return { available: false, source: "GBIF", record: null };
  }
}

async function getLiterature(scientificName: string) {
  const url = new URL("https://www.ebi.ac.uk/europepmc/webservices/rest/search");
  url.searchParams.set(
    "query",
    `EXT_ID:* AND TITLE_ABS:"${scientificName.replace(/["\\]/g, " ")}"`
  );
  url.searchParams.set("format", "json");
  url.searchParams.set("pageSize", "10");
  url.searchParams.set("resultType", "core");

  try {
    const data = await fetchJson(url.toString());

    return {
      available: true,
      source: "Europe PMC",
      sourceUrl: "https://europepmc.org/",
      totalResults: data.hitCount ?? 0,
      records: (data.resultList?.result ?? []).map((item: any) => ({
        title: item.title ?? null,
        authors: item.authorString ?? null,
        journal: item.journalTitle ?? null,
        year: item.pubYear ?? null,
        doi: item.doi ?? null,
        pmid: item.pmid ?? null,
        abstract: item.abstractText ?? null,
        url: item.doi
          ? `https://doi.org/${item.doi}`
          : item.pmid
            ? `https://pubmed.ncbi.nlm.nih.gov/${item.pmid}/`
            : item.id
              ? `https://europepmc.org/article/MED/${item.id}`
              : null,
      })),
    };
  } catch {
    return {
      available: false,
      source: "Europe PMC",
      sourceUrl: "https://europepmc.org/",
      totalResults: null,
      records: [],
    };
  }
}

export async function POST(request: NextRequest) {
  try {
    const contentType = request.headers.get("content-type") || "";
    let mode = "lifebook";
    let plantName = "";
    let imageBase64 = "";
    let mimeType = "";

    if (contentType.includes("multipart/form-data")) {
      const form = await request.formData();
      mode = String(form.get("mode") || "lifebook");
      plantName = String(form.get("plantName") || "").trim();

      const image = form.get("image");

      if (image instanceof File && image.size > 0) {
        if (!image.type.startsWith("image/")) {
          return NextResponse.json(
            { success: false, error: "Please upload a valid image." },
            { status: 400 }
          );
        }

        if (image.size > 10 * 1024 * 1024) {
          return NextResponse.json(
            { success: false, error: "Image size must not exceed 10 MB." },
            { status: 413 }
          );
        }

        mimeType = image.type;
        imageBase64 = Buffer.from(await image.arrayBuffer()).toString("base64");
      }
    } else {
      const body = await request.json();
      mode = typeof body.mode === "string" ? body.mode : "lifebook";
      plantName =
        typeof body.plantName === "string" ? body.plantName.trim() : "";
    }

    const allowedModes = [
      "medicinal",
      "edibility",
      "lifebook",
    ];

    if (!allowedModes.includes(mode)) {
      return NextResponse.json(
        { success: false, error: "Unsupported botanical workflow." },
        { status: 400 }
      );
    }

    if (!plantName && !imageBase64) {
      return NextResponse.json(
        {
          success: false,
          error: "Provide a plant name or upload a plant image.",
        },
        { status: 400 }
      );
    }

    if (plantName.length > 200) {
      return NextResponse.json(
        { success: false, error: "Plant name is too long." },
        { status: 400 }
      );
    }

    let candidates: PlantCandidate[] = [];

    if (imageBase64) {
      const apiKey = process.env.GEMINI_API_KEY;

      if (!apiKey) {
        return NextResponse.json(
          {
            success: false,
            error: "Image identification requires GEMINI_API_KEY.",
          },
          { status: 503 }
        );
      }

      candidates = await identifyFromImage(apiKey, imageBase64, mimeType);
    }

    if (plantName) {
      candidates.unshift({
        scientificName: plantName,
        commonName: "",
        confidence: "unverified",
        reasoning: "User-provided name; botanical identity has not been verified.",
      });
    }

    const uniqueCandidates = Array.from(
      new Map(
        candidates.map((candidate) => [
          candidate.scientificName.toLowerCase(),
          candidate,
        ])
      ).values()
    ).slice(0, 3);

    const investigations = await Promise.all(
      uniqueCandidates.map(async (candidate) => {
        const [taxonomy, literature] = await Promise.all([
          getTaxonomy(candidate.scientificName),
          getLiterature(candidate.scientificName),
        ]);

        return {
          candidate,
          taxonomy,
          literature,
        };
      })
    );

    return NextResponse.json({
      success: true,
      workflow: mode,
      generatedAt: new Date().toISOString(),
      identification: {
        method: imageBase64
          ? "AI-generated candidate suggestions; not definitive identification"
          : "User-provided plant name",
        candidates: uniqueCandidates,
      },
      investigations,
      assessment: {
        edibility: {
          status: "Uncertain",
          reason:
            "No authoritative, species-and-plant-part-specific food-safety verification has been performed.",
        },
        medicinalUse: {
          status: "Not established by this response",
          reason:
            "Retrieved literature must be reviewed individually. A publication or abstract does not by itself establish medicinal efficacy.",
        },
        compounds: {
          status: "Not retrieved",
          reason:
            "Taxonomy and literature records do not establish which compounds are present in a plant. Compound-specific evidence is required.",
        },
      },
      limitations: [
        "AI-generated image candidates may be incorrect.",
        "A GBIF taxonomic match does not prove image identity.",
        "Literature search results are not a substitute for full-text scientific appraisal.",
        "This response does not certify plant edibility or medical safety.",
      ],
    });
  } catch (error: any) {
    console.error("CureVerseAI botanical API error:", error);

    return NextResponse.json(
      {
        success: false,
        error:
          "The botanical investigation could not be completed.",
        message:
          process.env.NODE_ENV === "development"
            ? error?.message || "Unknown error"
            : undefined,
      },
      { status: 500 }
    );
  }
}
