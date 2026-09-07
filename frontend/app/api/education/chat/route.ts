import { NextRequest, NextResponse } from "next/server";
import { GoogleGenAI } from "@google/genai";

export const runtime = "nodejs";

const MODEL = "gemini-3.5-flash-lite";

const SYSTEM_INSTRUCTION = `
You are CureVerseAI Education Intelligence, the scientific education
assistant inside CureVerseAI.

Your purpose is to teach biology, biotechnology, computational biology,
genomics, molecular biology, drug development, and AI for biology.

CureVerseAI has five connected domains:
1. Research
2. Drug Development
3. Medicine
4. Biotechnology
5. Education

Research includes:
- Genes
- Proteins
- Variants
- Biological pathways
- Evidence reasoning
- Ensembl
- UniProt
- Reactome
- Open Targets
- ChEMBL
- ESM-2

Explain difficult scientific concepts clearly. Start with a simple
explanation and add technical depth when useful.

Important scientific rules:
- Never invent biological evidence.
- Never invent experimental results.
- Never fabricate citations or API results.
- Clearly distinguish established evidence, computational inference,
  hypothesis, and educational explanation.
- Do not pretend to have queried live Ensembl, UniProt, Reactome,
  Open Targets or ChEMBL data.
- If a user needs a live biological investigation, direct them toward
  the appropriate CureVerseAI Research tool.

Virtual Cell:
Explain it as an emerging computational concept for representing and
connecting molecular entities, cellular states, interactions, pathways,
and experimental observations.

Do not claim CureVerseAI has solved the complete Virtual Cell problem.

Educational medical boundary:
You may explain diseases, medicines, genetics, molecular mechanisms,
and clinical concepts educationally.
Do not diagnose users.
Do not prescribe medication.
Do not claim a treatment is appropriate for a particular person.

Response style:
- Give the direct answer first.
- Use short sections and bullets when useful.
- Define technical terms.
- Give examples when helpful.
- Keep normal answers reasonably concise.
`;

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const messages = Array.isArray(body?.messages)
      ? body.messages
      : [];

    if (messages.length === 0) {
      return NextResponse.json(
        {
          success: false,
          error: "No conversation messages were provided.",
        },
        { status: 400 }
      );
    }

    const apiKey = process.env.GEMINI_API_KEY;

    if (!apiKey) {
      return NextResponse.json(
        {
          success: false,
          error:
            "Gemini API key is not configured. Add GEMINI_API_KEY to .env.local.",
        },
        { status: 500 }
      );
    }

    const safeMessages = messages
      .slice(-20)
      .filter(
        (message: any) =>
          message &&
          (message.role === "user" || message.role === "model") &&
          typeof message.content === "string" &&
          message.content.trim().length > 0
      )
      .map((message: any) => ({
        role: message.role,
        parts: [{ text: message.content.trim() }],
      }));

    if (safeMessages.length === 0) {
      return NextResponse.json(
        {
          success: false,
          error: "Conversation is empty.",
        },
        { status: 400 }
      );
    }

    const ai = new GoogleGenAI({
      apiKey,
    });

    const response = await ai.models.generateContent({
      model: MODEL,
      contents: safeMessages,
      config: {
        systemInstruction: SYSTEM_INSTRUCTION,
        temperature: 0.45,
        maxOutputTokens: 900,
      },
    });

    const text =
      response.text?.trim() ||
      "I could not generate a response right now. Please try again.";

    return NextResponse.json({
      success: true,
      message: text,
      model: MODEL,
    });
  } catch (error: any) {
    console.error("CureVerseAI Gemini error:", error);

    return NextResponse.json(
      {
        success: false,
        error:
          error?.message ||
          "The CureVerseAI education engine could not respond.",
      },
      { status: 500 }
    );
  }
}
